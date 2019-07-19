import re

regex = re.compile(r"<@(\d+)>")
S = "1234 <@123> ывы <@456> <@789>"

for _id in regex.findall(S):
    print("id:", _id)


# a = regex.search(S)
# print(a[1])

# print(regex.sub(r"<@\1>", S))
