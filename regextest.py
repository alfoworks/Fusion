import re

regex = re.compile(r"\[id(\d+)\|(.*?)\]")
S = "1234 [id123|Хуй пизда] ывы [id456|asdkfds] [id789|..-]"

for (_id, name) in regex.findall(S):
    print("id:", _id, "name:", name)


# a = regex.search(S)
# print(a[1])

print(regex.sub(r"<@\1>", S))
