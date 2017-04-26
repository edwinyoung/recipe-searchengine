conversions = {
  'd': 1440,
  'h': 60,
  'm': 1
}

def str_to_time(time_string):
  minutes = 0
  time_string = time_string.lower()

  if len(time_string) > 0 and 'd' in time_string:
    time_string = map(str, time_string.split('d'))
    minutes += int(time_string[0]) * conversions['d']
    time_string = ''.join(time_string[1:])
    for i in range(len(time_string)):
      if time_string[i].isdigit():
        time_string = time_string[i:]
        break

  if len(time_string) > 0 and 'h' in time_string:
    time_string = time_string.split('h')
    minutes += int(time_string[0]) * conversions['h']
    for i in range(1, len(time_string)):
      if time_string[i].isdigit() or 'm' in time_string[i]:
        time_string = u''.join(time_string[i:])
        break

  if len(time_string) > 0 and 'm' in time_string:
    time_string = time_string.split('m')
    minutes += int(time_string[0]) * conversions['m']

  return minutes
