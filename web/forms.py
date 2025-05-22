from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired


class LocationSearchForm(FlaskForm):
    """Form for searching locations"""

    query = StringField("City or Location", validators=[DataRequired()])
    submit = SubmitField("Search")


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
        choices=[("C", "Celsius (°C)"), ("F", "Fahrenheit (°F)")],
        default="C",
    )
    submit = SubmitField("Update")


class ForecastDaysForm(FlaskForm):
    """Form for selecting number of forecast days (now as a dropdown)"""

    forecast_days = SelectField(
        "Forecast Days",
        choices=[("1", "1 Day"), ("3", "3 Days"), ("5", "5 Days"), ("7", "7 Days")],
        default="7",
    )
    submit = SubmitField("Update")
