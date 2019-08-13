import re

regex = re.compile(r"\[id(\d+)\|(.+?)\]")
S = "/123 [id168958515|@herobrine1st_erq]"

for _id in regex.findall(S):
    print("id:", _id)

print(regex.sub(r"<@\1>", S))
