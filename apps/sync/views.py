from django.shortcuts import render

# Create your views here.
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status

from apps.transactions.models import Transaction
from apps.transactions.serializers import TransactionSerializer
from apps.workspaces.models import Workspace


from django.utils import timezone
from .serializers import SyncTransactionSerializer
from django.db import IntegrityError
from apps.core.entitlements import get_entitlements
from .limits import get_limits
from apps.users.limits import get_limits



def _get_workspace_for_user(user, workspace_id):
    if workspace_id:
        return Workspace.objects.filter(id=workspace_id, memberships__user=user).first()

    # fallback to Personal
    return Workspace.objects.filter(created_by=user, name="Personal").first()


class SyncBootstrapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.query_params.get("workspace_id")
        ws = _get_workspace_for_user(request.user, workspace_id)
        if not ws:
            return Response({"detail": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        txns = Transaction.objects.filter(user=request.user, workspace=ws)
        ser = SyncTransactionSerializer(txns, many=True, context={"request": request})

        ent = get_entitlements(request.user, ws)

        if not ent["can_sync"]:
            return Response({"detail": "Sync not available for your plan."}, status=403)
        
        from apps.workspaces.models import Membership

        membership_exists = Membership.objects.filter(
        workspace_id=workspace_id,
        user=request.user
        ).exists()

        if not membership_exists:
            return Response(
            {"error": "You are not a member of this workspace."},
            status=403
            )
        
        membership = Membership.objects.get(
        workspace_id=workspace_id,
        user=request.user
        )
        
        if membership.role not in ["OWNER", "ADMIN"]:
            return Response(
            {"error": "You don't have permission to modify this workspace."},
            status=403
            )

        limits = get_limits(request.user, ws)

        return Response({
            "server_time": timezone.now().isoformat(),
            "workspace": {
                "id": ws.id,
                "name": ws.name,
                "workspace_type": ws.workspace_type,
            },
            "limits": limits,
            "transactions": ser.data
        })

class SyncPullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.query_params.get("workspace_id")
        since = request.query_params.get("since")          # optional ISO datetime
        cursor = request.query_params.get("cursor")        # optional "<iso>|<id>"
        limit = int(request.query_params.get("limit", 200))

        # safety cap
        limits = get_limits(request.user, ws)   # you need ws object here

        limit = min(limit, limits["pull_limit"])

        from apps.core.entitlements import get_entitlements, apply_history_window

        # after membership check and qs = Transaction.objects.filter(...)
        ws = Workspace.objects.filter(id=workspace_id_int).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=404)

        ent = get_entitlements(request.user, ws)
        if not ent["can_sync"]:
            return Response({"error": "Sync not available for your plan."}, status=403)

        # clamp limit by plan (client can ask for 9999, server says lol no)
        limit = max(1, min(limit, limits["pull_limit"]))

        # enforce plan history window BEFORE since/cursor logic
        qs = apply_history_window(qs, ent["history_days"])

        
        if not workspace_id:
            return Response({"error": "workspace_id is required"}, status=400)
        
        try:
            workspace_id_int = int(workspace_id)
        except (TypeError, ValueError):
            return Response({"error": "workspace_id must be an integer"}, status=400)



        from apps.workspaces.models import Membership

        # ✅ membership check
        if not Membership.objects.filter(user=request.user, workspace_id=workspace_id_int).exists():
            return Response({"error": "You don't belong to this workspace"}, status=403)

        qs = Transaction.objects.filter(workspace_id=workspace_id_int)

        # ✅ Apply "since" filter (first sync checkpoint)
        since_dt = parse_datetime(since) if since else None
        if since_dt:
            if timezone.is_naive(since_dt):
                since_dt = timezone.make_aware(since_dt, timezone.utc)
            qs = qs.filter(updated_at__gt=since_dt)


        # ✅ Apply cursor filter (continue from where last page ended)
        # cursor format: "<updated_at_iso>|<id>"
        if cursor:
            try:
                cursor_updated_at_str, cursor_id_str = cursor.split("|", 1)
                cursor_updated_at = parse_datetime(cursor_updated_at_str)
                cursor_id = int(cursor_id_str)

                if cursor_updated_at is None:
                    return Response({"error": "Invalid cursor datetime"}, status=400)
                
                if timezone.is_naive(cursor_updated_at):
                    cursor_updated_at = timezone.make_aware(cursor_updated_at, timezone.utc)


                # Continue AFTER the last item:
                # (updated_at > cursor_updated_at) OR (updated_at == cursor_updated_at AND id > cursor_id)
                qs = qs.filter(
                    Q(updated_at__gt=cursor_updated_at) |
                    Q(updated_at=cursor_updated_at, id__gt=cursor_id)
                )
            except ValueError:
                return Response({"error": "Invalid cursor format"}, status=400)

        # ✅ Stable ordering
        qs = qs.order_by("updated_at", "id")

        # Fetch limit + 1 so we know if there’s more
        items = list(qs[: limit + 1])
        has_more = len(items) > limit
        items = items[:limit]

        next_cursor = None
        if items:
            last = items[-1]
            next_cursor = f"{last.updated_at.isoformat()}|{last.id}"

        ser = SyncTransactionSerializer(items, many=True, context={"request": request})

        return Response({
            "workspace_id": int(workspace_id),
            "server_time": timezone.now().isoformat(),
            "limit": limit,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "transactions": ser.data,
        })

class SyncPushView(APIView):
    permission_classes = [IsAuthenticated]
    

    def post(self, request):
        workspace_id = request.data.get("workspace_id")
        txns = request.data.get("transactions", [])

        from apps.workspaces.models import Membership

        
        if not workspace_id:
            return Response({"error": "workspace_id is required"}, status=400)

        membership_exists = Membership.objects.filter(
        workspace_id=workspace_id,
        user=request.user
        ).exists()

        if not membership_exists:
            return Response(
            {"error": "You are not a member of this workspace."},
            status=403
            )
        
        membership = Membership.objects.get(
        workspace_id=workspace_id,
        user=request.user
        )
        
        if membership.role not in ["OWNER", "ADMIN"]:
            return Response(
            {"error": "You don't have permission to modify this workspace."},
            status=403
            )
        
        member_count = Membership.objects.filter(workspace_id=workspace_id).count()
        if member_count > limits["max_members"]:
            return Response({"error": "Workspace member limit exceeded for your plan."}, status=403)


        acks = []
        conflicts = []

        from apps.core.entitlements import get_entitlements

        ws = Workspace.objects.filter(id=workspace_id).first()
        if not ws:
            return Response({"error": "Workspace not found"}, status=404)

        limits = get_limits(request.user, ws)

        if len(txns) > limits["push_max_items"]:
            return Response(
                {"error": f"Too many items in one push. Max is {limits['push_max_items']} for your plan/workspace."},
                status=400
            )

        ent = get_entitlements(request.user, ws)

        if not ent["can_sync"]:
            return Response({"error": "Sync not available for your plan."}, status=403)

        if not ent["can_push"]:
            return Response({"error": "Sync push is not allowed on your plan."}, status=403)

        # limit payload size by plan (prevents nuking server with 10k transactions)
        if len(txns) > limits["push_max_items"]:
            return Response({"error": "Sync push limit exceeded for your plan."}, status=403)


        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            for item in txns:
                client_id = item.get("client_id")
                incoming_version = int(item.get("version", 1))

                if not client_id:
                    continue

                obj = Transaction.objects.filter(
                    workspace_id=workspace_id,
                    client_id=client_id
                ).first()

                # CREATE
                if not obj:
                    serializer = SyncTransactionSerializer(data=item, context={"request": request})
                    serializer.is_valid(raise_exception=True)

                    try:
                        new_obj = serializer.save(
                            user=request.user,
                            workspace_id=workspace_id,
                            version=1
                        )

                        acks.append({
                            "client_id": str(new_obj.client_id),
                            "status": "saved",
                            "server_id": new_obj.id,
                            "server_version": new_obj.version,
                            "server_updated_at": new_obj.updated_at,
                        })
                        continue

                    except IntegrityError: 
                        # Someone else created it in the same moment.
                        obj = Transaction.objects.filter(
                            workspace_id=workspace_id,
                            client_id=client_id
                        ).first()

                        if not obj:
                            # Super rare, but keeps you safe.
                            raise
                        # fall through to version checks / update logic below

                # DELETE REQUEST (must be inside loop)
                incoming_deleted_at = item.get("deleted_at")
                if incoming_deleted_at is not None:
                    if incoming_version != obj.version + 1:
                        conflicts.append({
                            "client_id": str(obj.client_id),
                            "server_version": obj.version,
                            "incoming_version": incoming_version
                        })
                        acks.append({
                            "client_id": str(obj.client_id),
                            "status": "conflict",
                            "server_version": obj.version,
                            "server_updated_at": obj.updated_at,
                        })
                        continue

                    obj.deleted_at = timezone.now()
                    obj.version = incoming_version
                    obj.save(update_fields=["deleted_at", "version", "updated_at"])

                    acks.append({
                        "client_id": str(obj.client_id),
                        "status": "saved",
                        "server_id": obj.id,
                        "server_version": obj.version,
                        "server_updated_at": obj.updated_at,
                    })
                    continue

                # STRICT VERSION CHECK
                if incoming_version != obj.version + 1:
                    conflicts.append({
                        "client_id": str(obj.client_id),
                        "server_version": obj.version,
                        "incoming_version": incoming_version
                    })
                    acks.append({
                        "client_id": str(obj.client_id),
                        "status": "conflict",
                        "server_version": obj.version,
                        "server_updated_at": obj.updated_at,
                    })
                    continue

                # UPDATE
                serializer = SyncTransactionSerializer(
                    obj, data=item, partial=True, context={"request": request}
                )
                serializer.is_valid(raise_exception=True)
                updated_obj = serializer.save(version=incoming_version)

                acks.append({
                    "client_id": str(updated_obj.client_id),
                    "status": "saved",
                    "server_id": updated_obj.id,
                    "server_version": updated_obj.version,
                    "server_updated_at": updated_obj.updated_at,
                })


            return Response({
                "acks": acks,
                "conflicts": conflicts
                })

