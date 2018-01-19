import datetime

start = datetime.datetime.strptime('2014-01-01', '%Y-%m-%d').date()
end = datetime.date.today()
interval = int(int((end - start).days) / 90) + 1
ninedays = datetime.timedelta(days=90)

for i in range(0, interval):
    if i != 0:
        j = 1
    start_day = start + ninedays * i
    if i == interval - 1:
        end_day = datetime.date.today()
    else:
        end_day = start_day + ninedays

    print(start_day, end_day)