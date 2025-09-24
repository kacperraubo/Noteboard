from django.forms import Form


def get_error_message_from(form: Form):
    error_message = form.errors.as_text().split("*")[-1]
    return error_message


def get_error_message_and_field_from(form: Form):
    errors = list()
    for field, message in form.errors.items():
        temp = dict()
        temp[field] = message[0]
        errors.append(temp)
    return errors
