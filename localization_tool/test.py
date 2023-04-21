src ={
  "appName": "HelpOS Employee",

  "companyName": "Security-online",

  "drawerHome": "Home",
  "drawerTables": "Tables"

}
json_to_list = list(src.items())
keys_str = '___'.join([pair[1] for pair in json_to_list])
print(keys_str)
translated_values = keys_str.split('___')
print(translated_values)
translated_arb = {}
for index, value in enumerate(json_to_list):
  translated_arb[value[0]] = translated_values[index]

print(translated_arb)