import re


a = "	11元/公斤	"
aa = re.match(".*?(\d+).*", a).group(1)
print(aa)