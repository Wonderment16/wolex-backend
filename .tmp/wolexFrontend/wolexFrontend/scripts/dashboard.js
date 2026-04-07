const token = localStorage.getItem("access");

async function loadDashboard() {

  try {

    const response = await fetch("http://127.0.0.1:8000/api/users/context", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await response.json();

    console.log(data);

  } catch (err) {

    console.error("Dashboard failed to load");

  }

}

loadDashboard();