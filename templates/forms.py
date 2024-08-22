import datetime as dt

from flask import Response
from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SubmitField, DateField


class DownloadButtonForm(FlaskForm):
    submit_download = SubmitField('Download')

    @classmethod
    def generate_request_with_dataframe_csv(cls, dataframe_to_download, filename=None):
        if filename is None:
            current_time = dt.datetime.now(pytz.utc)
            file_iso = current_time.strftime("%Y%m%dT%H%M")
            filename = f"{file_iso} - StaasDownload"
        filename = filename.replace('.csv', '')
        return Response(
            dataframe_to_download.to_csv(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}.csv"},
        )


class PeriodFromPeriodToForm(FlaskForm):
    period_from = DateTimeLocalField('From:', format='%Y-%m-%dT%H:%M')
    period_to = DateTimeLocalField('To:', format='%Y-%m-%dT%H:%M')
    submit_date = SubmitField('Edit Dates')

    def validate(self, **kwargs):
        """Validate the datetimes in the form"""
        # Standard validators
        rv = FlaskForm.validate(self)
        # Ensure all standard validators are met
        if rv:
            # Ensure period_from is not in the future
            if self.period_from.data > dt.datetime.now():
                self.period_from.errors.append('Period From cannot be set into the future.')
                return False
            # Ensure period_to > period_from
            if self.period_from.data >= self.period_to.data:
                self.period_to.errors.append('Period To must be set after Period From.')
                return False
            return True
        return False


class PeriodFromPeriodToFormDate(FlaskForm):
    period_from = DateField('From:', format='%Y-%m-%d')
    period_to = DateField('To:', format='%Y-%m-%d')
    submit_date = SubmitField('Edit Dates')

    def validate(self, **kwargs):
        """Validate the datetimes in the form"""
        # Standard validators
        rv = FlaskForm.validate(self)
        # Ensure all standard validators are met
        if rv:
            # Ensure period_from is not in the future
            if self.period_from.data > dt.date.today():
                self.period_from.errors.append('Period From cannot be set into the future.')
                return False
            # Ensure period_to > period_from
            if self.period_from.data >= self.period_to.data:
                self.period_to.errors.append('Period To must be set after Period From.')
                return False
            return True
        return False
