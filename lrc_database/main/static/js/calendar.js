document.addEventListener('DOMContentLoaded', function () {
  let calendarEl = document.getElementById('calendar');
  let height = Math.max(
    document.getElementById('main-div').offsetHeight - document.getElementById("cal-header").offsetHeight,
    document.getElementById('cal-div').offsetWidth);
  let calendar = new FullCalendar.Calendar(calendarEl, {
    themeSystem: 'bootstrap',
    initialView: 'dayGridMonth',
    themeSystem: 'bootstrap5',
    eventSources: eventSources,
    expandRows: true,
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    },
    height:`${height}px`
  });
  calendar.render();
});
