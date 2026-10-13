from django.views.generic import TemplateView


class TutorialView(TemplateView):
    """Browser-only Python tutorial (see docs/tutorial/README.md).

    Deliberate exception to the "use HTMX for all dynamic updates" guideline:
    after this one GET, the page makes no requests to the Django app. No API
    endpoints, no HTMX, no form posts, no telemetry. Learner code runs in a
    Pyodide worker, the task bank is a static file, and progress lives in
    localStorage. No database access, no login, no consent gate.
    """

    template_name = "tutorial/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Blank the Rollbar client token so base.html leaves out the browser
        # error reporter: nothing about the learner's session leaves the machine.
        context["rollbar_client_token"] = ""
        return context
