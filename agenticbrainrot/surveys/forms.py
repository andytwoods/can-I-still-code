from django import forms


class ScaleWidget(forms.NumberInput):
    """Range input with min/mid/max labels displayed."""

    template_name = "surveys/widgets/scale.html"

    def __init__(
        self, *, scale_min, scale_max, min_label, mid_label, max_label, **kwargs,
    ):
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.min_label = min_label
        self.mid_label = mid_label
        self.max_label = max_label
        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"].update({
            "scale_min": self.scale_min,
            "scale_max": self.scale_max,
            "min_label": self.min_label,
            "mid_label": self.mid_label,
            "max_label": self.max_label,
        })
        return context


def build_survey_form(questions_qs):
    """
    Build a Django Form class dynamically from a queryset of SurveyQuestion.

    Field names use ``question_{pk}`` so the view can map answers back.
    """
    fields = {}

    for q in questions_qs:
        field_name = f"question_{q.pk}"
        common = {
            "label": q.text,
            "help_text": q.help_text,
            "required": q.is_required,
        }

        if q.question_type == "text":
            fields[field_name] = forms.CharField(
                widget=forms.TextInput(attrs={"class": "input"}),
                **common,
            )

        elif q.question_type == "number":
            fields[field_name] = forms.IntegerField(
                widget=forms.NumberInput(attrs={"class": "input"}),
                **common,
            )

        elif q.question_type == "single_choice":
            choices = [(c[0], c[1]) for c in (q.choices or [])]
            fields[field_name] = forms.ChoiceField(
                widget=forms.RadioSelect,
                choices=choices,
                **common,
            )

        elif q.question_type == "multi_choice":
            choices = [(c[0], c[1]) for c in (q.choices or [])]
            fields[field_name] = forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple,
                choices=choices,
                **common,
            )

        elif q.question_type == "scale":
            fields[field_name] = forms.IntegerField(
                min_value=q.scale_min,
                max_value=q.scale_max,
                widget=ScaleWidget(
                    scale_min=q.scale_min,
                    scale_max=q.scale_max,
                    min_label=q.min_label or "",
                    mid_label=q.mid_label or "",
                    max_label=q.max_label or "",
                    attrs={
                        "type": "range",
                        "min": q.scale_min,
                        "max": q.scale_max,
                        "step": 1,
                        "class": "slider",
                    },
                ),
                **common,
            )

    return type("SurveyForm", (forms.Form,), fields)
