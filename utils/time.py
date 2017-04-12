
conversions = {
  'd': 1440,
  'h': 60,
  'm': 1
}

def str_to_time(time_string):
  minutes = 0
  time_string = time_string.lower()
  if len(time_string) > 0 and time_string.split('d')[0] != time_string:
    time_string = time_string.split('d')
    minutes += int(time_string[0]) * conversions['d']
    time_string = u''.join(time_string[1:])

  if len(time_string) > 0 and time_string.split('h')[0] != time_string:
    time_string = time_string.split('h')
    minutes += int(time_string[0]) * conversions['h']
    time_string = u''.join(time_string[1:])

  if len(time_string) > 0 and time_string.split('m')[0] != time_string:
    time_string = time_string.split('m')
    minutes += int(time_string[0]) * conversions['m']

  return minutes