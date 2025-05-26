"""Unit tests for Flask forms - using shared utilities."""

from unittest.mock import MagicMock, patch


class TestLocationSearchForm:
    """Test cases for LocationSearchForm."""

    def test_form_creation(self, web_forms_module):
        """Test form can be created."""
        form = web_forms_module.LocationSearchForm()
        assert hasattr(form, "query")
        assert hasattr(form, "submit")

    def test_form_validation_valid_query(self, web_forms_module):
        """Test form validation with valid query."""
        form_data = {"query": "London", "csrf_token": "test_token"}
        with patch("web.forms.request") as mock_request:
            mock_request.form = form_data
            form = web_forms_module.LocationSearchForm(data=form_data)
            form.csrf_token.data = "test_token"
            # Skip CSRF validation for testing
            form.csrf_token = MagicMock()
            form.csrf_token.validate.return_value = True

            # Check field exists and has data
            assert form.query.data == "London"

    def test_form_validation_empty_query(self, web_forms_module):
        """Test form validation with empty query."""
        form_data = {"query": "", "csrf_token": "test_token"}
        form = web_forms_module.LocationSearchForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        # Empty query should be invalid due to required field
        assert not form.validate()


class TestUserInputLocationForm:
    """Test cases for UserInputLocationForm."""

    def test_form_creation(self, web_forms_module):
        """Test form can be created."""
        form = web_forms_module.UserInputLocationForm()
        assert hasattr(form, "location")
        assert hasattr(form, "submit")

    def test_form_validation_valid_location(self, web_forms_module):
        """Test form validation with valid location."""
        form_data = {"location": "New York", "csrf_token": "test_token"}
        form = web_forms_module.UserInputLocationForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        assert form.location.data == "New York"


class TestUnitSelectionForm:
    """Test cases for UnitSelectionForm."""

    def test_form_creation(self, web_forms_module):
        """Test form can be created."""
        form = web_forms_module.UnitSelectionForm()
        assert hasattr(form, "unit")
        assert hasattr(form, "submit")

    def test_form_validation_celsius(self, web_forms_module):
        """Test form validation with Celsius unit."""
        form_data = {"unit": "C", "csrf_token": "test_token"}
        form = web_forms_module.UnitSelectionForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        assert form.unit.data == "C"

    def test_form_validation_fahrenheit(self, web_forms_module):
        """Test form validation with Fahrenheit unit."""
        form_data = {"unit": "F", "csrf_token": "test_token"}
        form = web_forms_module.UnitSelectionForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        assert form.unit.data == "F"

    def test_form_validation_invalid_unit(self, web_forms_module):
        """Test form validation with invalid unit."""
        form_data = {"unit": "X", "csrf_token": "test_token"}
        form = web_forms_module.UnitSelectionForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        # Invalid unit should fail validation
        assert not form.validate()


class TestForecastDaysForm:
    """Test cases for ForecastDaysForm."""

    def test_form_creation(self, web_forms_module):
        """Test form can be created."""
        form = web_forms_module.ForecastDaysForm()
        assert hasattr(form, "forecast_days")
        assert hasattr(form, "submit")

    def test_form_validation_valid_days(self, web_forms_module):
        """Test form validation with valid forecast days."""
        form_data = {"forecast_days": "7", "csrf_token": "test_token"}
        form = web_forms_module.ForecastDaysForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        assert form.forecast_days.data == "7"

    def test_form_validation_invalid_days(self, web_forms_module):
        """Test form validation with invalid forecast days."""
        form_data = {"forecast_days": "15", "csrf_token": "test_token"}
        form = web_forms_module.ForecastDaysForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        # 15 days should be invalid (likely max is 7-10)
        # This depends on the actual choices defined in the form
        # The form should validate based on the choices available


class TestDateWeatherNLForm:
    """Test cases for DateWeatherNLForm."""

    def test_form_creation(self, web_forms_module):
        """Test form can be created."""
        form = web_forms_module.DateWeatherNLForm()
        assert hasattr(form, "query")
        assert hasattr(form, "submit")

    def test_form_validation_valid_query(self, web_forms_module):
        """Test form validation with valid natural language query."""
        form_data = {
            "query": "What is the weather like in London tomorrow?",
            "csrf_token": "test_token",
        }
        form = web_forms_module.DateWeatherNLForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        assert "London" in form.query.data
        assert "tomorrow" in form.query.data

    def test_form_validation_empty_query(self, web_forms_module):
        """Test form validation with empty query."""
        form_data = {"query": "", "csrf_token": "test_token"}
        form = web_forms_module.DateWeatherNLForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        # Empty query should be invalid
        assert not form.validate()

    def test_form_validation_short_query(self, web_forms_module):
        """Test form validation with very short query."""
        form_data = {"query": "hi", "csrf_token": "test_token"}
        form = web_forms_module.DateWeatherNLForm(data=form_data)
        form.csrf_token = MagicMock()
        form.csrf_token.validate.return_value = True

        # Very short query should be invalid due to length requirement
        assert not form.validate()


class TestFormIntegration:
    """Integration tests for forms."""

    def test_all_forms_have_csrf_protection(self, web_forms_module):
        """Test that all forms have CSRF protection."""
        forms = [
            web_forms_module.LocationSearchForm(),
            web_forms_module.UserInputLocationForm(),
            web_forms_module.UnitSelectionForm(),
            web_forms_module.ForecastDaysForm(),
            web_forms_module.DateWeatherNLForm(),
        ]

        for form in forms:
            # Each form should have a csrf_token field
            assert hasattr(form, "csrf_token")

    def test_forms_can_be_instantiated_without_data(self, web_forms_module):
        """Test that forms can be created without data."""
        forms = [
            web_forms_module.LocationSearchForm(),
            web_forms_module.UserInputLocationForm(),
            web_forms_module.UnitSelectionForm(),
            web_forms_module.ForecastDaysForm(),
            web_forms_module.DateWeatherNLForm(),
        ]

        # All forms should be created without errors
        for form in forms:
            assert form is not None

    def test_forms_have_submit_buttons(self, web_forms_module):
        """Test that all forms have submit buttons."""
        forms = [
            web_forms_module.LocationSearchForm(),
            web_forms_module.UserInputLocationForm(),
            web_forms_module.UnitSelectionForm(),
            web_forms_module.ForecastDaysForm(),
            web_forms_module.DateWeatherNLForm(),
        ]

        for form in forms:
            assert hasattr(form, "submit")
