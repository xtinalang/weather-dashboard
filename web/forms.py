from flask_wtf import FlaskForm
from wtforms import (
    RadioField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

from .utils import (
    CELSIUS,
    DEFAULT_FORECAST_DAYS_STR,
    FORECAST_DAYS_CHOICES,
    TEMPERATURE_UNIT_CHOICES,
)


class LocationSearchForm(FlaskForm):
    """Form for searching locations"""

    query = StringField("City or Location", validators=[DataRequired()])
    submit = SubmitField("Search")


class UserInputLocationForm(FlaskForm):
    """Form for directly entering a location"""

    location = StringField("Enter City Name", validators=[DataRequired()])
    submit = SubmitField("Get Weather")


class UnitSelectionForm(FlaskForm):
    """Form for selecting temperature unit"""

    unit = RadioField(
        "Temperature Unit",
        choices=TEMPERATURE_UNIT_CHOICES,
        default=CELSIUS,
    )
    submit = SubmitField("Update")


class ForecastDaysForm(FlaskForm):
    """Form for selecting number of forecast days (now as a dropdown)"""

    forecast_days = SelectField(
        "Forecast Days",
        choices=FORECAST_DAYS_CHOICES,
        default=DEFAULT_FORECAST_DAYS_STR,
    )
    submit = SubmitField("Update")


class DateWeatherNLForm(FlaskForm):
    query = StringField("Ask about the weather", validators=[DataRequired()])
    submit = SubmitField("Get Weather")
