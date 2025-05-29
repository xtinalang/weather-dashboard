from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
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


class LocationSelectionForm(FlaskForm):
    """Form for selecting a location from search results"""

    selected_location = RadioField("Select Location", validators=[DataRequired()])
    action = HiddenField("Action")  # 'weather' or 'forecast'
    unit = HiddenField("Unit")
    forecast_days = HiddenField("Forecast Days")
    submit = SubmitField("Get Weather")


class UserInputLocationForm(FlaskForm):
    """Form for directly entering a location"""

    location = StringField("Enter City Name", validators=[DataRequired()])
    submit = SubmitField("Get Weather")


class DateWeatherForm(FlaskForm):
    location = StringField("todo ... ", validators=[DataRequired()])


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
