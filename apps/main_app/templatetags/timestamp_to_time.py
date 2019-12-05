from django import template
import datetime
register = template.Library()    

@register.filter('timestamp_to_time')
def convert_timestamp_to_time(timestamp):
    import time
    return datetime.datetime.fromtimestamp(timestamp-14400).strftime('%m/%d %H:%M')

@register.filter('timestamp_to_date')
def convert_timestamp_to_time(timestamp):
    import time
    return datetime.datetime.fromtimestamp(timestamp-14400).strftime('%Y-%m-%d')

@register.filter('upcoming')
def upcoming(timestamp):
    import time
    return (timestamp-time.time())

@register.filter('percentage')
def percentage(winpercentage):
    percent = int(winpercentage*100)
    return f"{percent}%"