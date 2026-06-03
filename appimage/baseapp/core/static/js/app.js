function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

document.addEventListener("htmx:configRequest", (event) => {
  event.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
});

document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("starter-chart");
  if (!canvas || !window.Chart) {
    return;
  }

  new window.Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Django", "Tailwind", "htmx"],
      datasets: [
        {
          label: "Template defaults",
          data: [5, 4, 3],
          backgroundColor: ["#0f172a", "#2563eb", "#16a34a"],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
});
