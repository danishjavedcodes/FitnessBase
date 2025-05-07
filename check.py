# import hashlib

# def generate_service_account_dict():
#     # Step 1: Break down the parts
#     private_key_part1 = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe"
#     private_key_part2 = "\nefWF/PgmNmriNNZxyb1euBtdjQAGMHv0w1yuF+4XzGu22T6fyp+PHEeZdYCpsAZS"
#     private_key_part3 = "\nFwD7qsrctXZWUNyay6vjYEzt1ufzUPpNGaSn+vtDNbigaFpSEUygYRJRslKiO55G"
#     private_key_part4 = "\nsiKfNArdIVz93qRAQenxgo6UHmi+7i7+6+ZfZMJdhoSg0OH+fZI/jTPpHmyynmwX"
#     private_key_part5 = "\nLB4VyveEECWXkNPNZZ8lhXAkd3H+tWsxS4t9nTOrdjrbBnp/yHYlQHDPRipf6FFH"
#     private_key_part6 = "\newdMzIbuMf8mVI1i/edZlt5sa5hD5d5OFMZsCaiPWYTiDF2LRohJwCCrtrQyameV"
#     private_key_part7 = "\nRExs0M0XAgMBAAECggEAEUPaSJ4gXzr1BTnx6qUCZAK5zHWu0kB/tQNziF/1Qx8R"
#     private_key_part8 = "\n05mLA784v6CYQCn5NgNFdE5s7ihKWa2hVy5RHhOLNyXZBKlAOvuFxVzpXBCUw+SY"
#     private_key_part9 = "\n8f53DsSs9fSW/+k/n1Qq7LlO+jfr4BpzAuI/4dCA6ITsNtXmDB/qMyeKNRfdrWs9"
#     private_key_part10 = "\nE+p+LjAbN9TX6WGKqx9NuhaPTv0JOLsDTfRXd9cpEIcAq50gkVTXtUEFVL4/2V1K"
#     private_key_part11 = "\n33PfGV6djJdf2aa6J/gOUNav+P9/WOE5qiTaXpRU38yEhDFme8LXuBhc1h71tzTs"
#     private_key_part12 = "\nzQcnYfsh0PncQKsj+ntQqMtd1ShXfsFwmKoTr27y/QKBgQDdlw83MT43VpRPnl30"
#     private_key_part13 = "\nZtOkgpUC3pkMHInZFW8Mj3dDzL18km6qFgGAKai4829/S6sSCNSjn42vtQh55WdF"
#     private_key_part14 = "\ndHiQrIjRsWJk6c2OilqILZ0to+1XgTT+7069HkWsBRDPP4cRuQ19YS1DzAxd6H9N"
#     private_key_part15 = "\n4O8TVJZNDpQCVM86pzGrvPmEXQKBgQDVEVbAaazy1O1dFCLTI0oPniY7+noE1QWu"
#     private_key_part16 = "\n7iRL5lBTfJGm/AgVSvtmPfKZAVPBLAq0+zOj5D+BKIZXE7Xmj+PDhjyQSDrI6naX"
#     private_key_part17 = "\nnqbeqGbRwajcuDBZ3NQp1oCNc7UPisXgqV15t8hTGBbrPeyzE2dwclXXytxUj48k"
#     private_key_part18 = "\nv0hyizFAAwKBgCznrOSxbPtH51xPKpkZsXAYKlxfgcJrkh/U8SEpfbDWr9urzRNY"
#     private_key_part19 = "\nzEsNpix84K56RhusgHL8JXljBWm2bHwtwzUGUd+0w8zReJ+XOAt6uuyB2Novy+6R"
#     private_key_part20 = "\nznISzWmzyRlGtXeI+cvbwpGHq0XolMvSdoCDVsYc2y+xwiEPusgjzqjdAoGBAKA3"
#     private_key_part21 = "\nvpVHoa6kYK0KVDmSosFlufiGHDT//psRJigQ0zxEQr5fbLCeRrcWRBO8BMAQnyiC"
#     private_key_part22 = "\ncM1/+CTmVUarYrAyaSIBEg+o0NN+Q5k1yuNJnK+EQbdfpbQdM0kWrGoxpOhAARY0"
#     private_key_part23 = "\nJT8+7JtXVPyl/xSVtcW/pD91owLPRONsF01Sz8EDAoGBALYXqViV6FvfTKrjQG6D"
#     private_key_part24 = "\nchCDghsej8EJqgNfyNJ3M+QXyKAUVXwX1WH78OCqbWzHnuCSQedyFfvVkSrouLDm"
#     private_key_part25 = "\n4Z3PLL22fY1NuOGJp5YPuy7Ohb3CbU4kGp5Y8ne4peFJiZecgQYH54mGkhdTCaZb"
#     private_key_part26 = "\nA9Oo2xQLmTYUfoMegDEUQKIJ\n-----END PRIVATE KEY-----\n"
    
#     private_key = ''.join([private_key_part1, private_key_part2, private_key_part3, private_key_part4, private_key_part5, private_key_part6, private_key_part7, private_key_part8,
#                           private_key_part9, private_key_part10, private_key_part11, private_key_part12, private_key_part13, private_key_part14, private_key_part15, private_key_part16,
#                           private_key_part17, private_key_part18, private_key_part19, private_key_part20, private_key_part21, private_key_part22, private_key_part23, private_key_part24,
#                           private_key_part25, private_key_part26])

#     # Step 2: Construct the final dictionary
#     service_account_dict = {
#         "type": "service_account",
#         "project_id": "fitnessbase",
#         "private_key_id": "39b6404749200119068d6be19355d3fbab39b94e",
#         "private_key": private_key,
#         "client_email": "fitnessbase@fitnessbase.iam.gserviceaccount.com",
#         "client_id": "103983109866240256974",
#         "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#         "token_uri": "https://oauth2.googleapis.com/token",
#         "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#         "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fitnessbase%40fitnessbase.iam.gserviceaccount.com",
#         "universe_domain": "googleapis.com"
#     }
    
#     return service_account_dict

# def validate_service_account_dict(generated_dict):
#     expected_dict = {
#             "type": "service_account",
#             "project_id": "fitnessbase",
#             "private_key_id": "39b6404749200119068d6be19355d3fbab39b94e",
#             "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe\nefWF/PgmNmriNNZxyb1euBtdjQAGMHv0w1yuF+4XzGu22T6fyp+PHEeZdYCpsAZS\nFwD7qsrctXZWUNyay6vjYEzt1ufzUPpNGaSn+vtDNbigaFpSEUygYRJRslKiO55G\nsiKfNArdIVz93qRAQenxgo6UHmi+7i7+6+ZfZMJdhoSg0OH+fZI/jTPpHmyynmwX\nLB4VyveEECWXkNPNZZ8lhXAkd3H+tWsxS4t9nTOrdjrbBnp/yHYlQHDPRipf6FFH\newdMzIbuMf8mVI1i/edZlt5sa5hD5d5OFMZsCaiPWYTiDF2LRohJwCCrtrQyameV\nRExs0M0XAgMBAAECggEAEUPaSJ4gXzr1BTnx6qUCZAK5zHWu0kB/tQNziF/1Qx8R\n05mLA784v6CYQCn5NgNFdE5s7ihKWa2hVy5RHhOLNyXZBKlAOvuFxVzpXBCUw+SY\n8f53DsSs9fSW/+k/n1Qq7LlO+jfr4BpzAuI/4dCA6ITsNtXmDB/qMyeKNRfdrWs9\nE+p+LjAbN9TX6WGKqx9NuhaPTv0JOLsDTfRXd9cpEIcAq50gkVTXtUEFVL4/2V1K\n33PfGV6djJdf2aa6J/gOUNav+P9/WOE5qiTaXpRU38yEhDFme8LXuBhc1h71tzTs\nzQcnYfsh0PncQKsj+ntQqMtd1ShXfsFwmKoTr27y/QKBgQDdlw83MT43VpRPnl30\nZtOkgpUC3pkMHInZFW8Mj3dDzL18km6qFgGAKai4829/S6sSCNSjn42vtQh55WdF\ndHiQrIjRsWJk6c2OilqILZ0to+1XgTT+7069HkWsBRDPP4cRuQ19YS1DzAxd6H9N\n4O8TVJZNDpQCVM86pzGrvPmEXQKBgQDVEVbAaazy1O1dFCLTI0oPniY7+noE1QWu\n7iRL5lBTfJGm/AgVSvtmPfKZAVPBLAq0+zOj5D+BKIZXE7Xmj+PDhjyQSDrI6naX\nnqbeqGbRwajcuDBZ3NQp1oCNc7UPisXgqV15t8hTGBbrPeyzE2dwclXXytxUj48k\nv0hyizFAAwKBgCznrOSxbPtH51xPKpkZsXAYKlxfgcJrkh/U8SEpfbDWr9urzRNY\nzEsNpix84K56RhusgHL8JXljBWm2bHwtwzUGUd+0w8zReJ+XOAt6uuyB2Novy+6R\nznISzWmzyRlGtXeI+cvbwpGHq0XolMvSdoCDVsYc2y+xwiEPusgjzqjdAoGBAKA3\nvpVHoa6kYK0KVDmSosFlufiGHDT//psRJigQ0zxEQr5fbLCeRrcWRBO8BMAQnyiC\ncM1/+CTmVUarYrAyaSIBEg+o0NN+Q5k1yuNJnK+EQbdfpbQdM0kWrGoxpOhAARY0\nJT8+7JtXVPyl/xSVtcW/pD91owLPRONsF01Sz8EDAoGBALYXqViV6FvfTKrjQG6D\nchCDghsej8EJqgNfyNJ3M+QXyKAUVXwX1WH78OCqbWzHnuCSQedyFfvVkSrouLDm\n4Z3PLL22fY1NuOGJp5YPuy7Ohb3CbU4kGp5Y8ne4peFJiZecgQYH54mGkhdTCaZb\nA9Oo2xQLmTYUfoMegDEUQKIJ\n-----END PRIVATE KEY-----\n",
#             "client_email": "fitnessbase@fitnessbase.iam.gserviceaccount.com",
#             "client_id": "103983109866240256974",
#             "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#             "token_uri": "https://oauth2.googleapis.com/token",
#             "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#             "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fitnessbase%40fitnessbase.iam.gserviceaccount.com",
#             "universe_domain": "googleapis.com"
#         }
    
#     return generated_dict == expected_dict

# # Generate the dictionary
# generated_dict = generate_service_account_dict()

# # Validate the generated dictionary
# is_valid = validate_service_account_dict(generated_dict)
# print(f"Is the generated dictionary valid? {is_valid}")


private_key_part1 = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe"
#     private_key_part2 = "\nefWF/PgmNmriNNZxyb1euBtdjQAGMHv0w1yuF+4XzGu22T6fyp+PHEeZdYCpsAZS"
#     private_key_part3 = "\nFwD7qsrctXZWUNyay6vjYEzt1ufzUPpNGaSn+vtDNbigaFpSEUygYRJRslKiO55G"
#     private_key_part4 = "\nsiKfNArdIVz93qRAQenxgo6UHmi+7i7+6+ZfZMJdhoSg0OH+fZI/jTPpHmyynmwX"
#     private_key_part5 = "\nLB4VyveEECWXkNPNZZ8lhXAkd3H+tWsxS4t9nTOrdjrbBnp/yHYlQHDPRipf6FFH"
#     private_key_part6 = "\newdMzIbuMf8mVI1i/edZlt5sa5hD5d5OFMZsCaiPWYTiDF2LRohJwCCrtrQyameV"
#     private_key_part7 = "\nRExs0M0XAgMBAAECggEAEUPaSJ4gXzr1BTnx6qUCZAK5zHWu0kB/tQNziF/1Qx8R"
#     private_key_part8 = "\n05mLA784v6CYQCn5NgNFdE5s7ihKWa2hVy5RHhOLNyXZBKlAOvuFxVzpXBCUw+SY"
#     private_key_part9 = "\n8f53DsSs9fSW/+k/n1Qq7LlO+jfr4BpzAuI/4dCA6ITsNtXmDB/qMyeKNRfdrWs9"
#     private_key_part10 = "\nE+p+LjAbN9TX6WGKqx9NuhaPTv0JOLsDTfRXd9cpEIcAq50gkVTXtUEFVL4/2V1K"
#     private_key_part11 = "\n33PfGV6djJdf2aa6J/gOUNav+P9/WOE5qiTaXpRU38yEhDFme8LXuBhc1h71tzTs"
#     private_key_part12 = "\nzQcnYfsh0PncQKsj+ntQqMtd1ShXfsFwmKoTr27y/QKBgQDdlw83MT43VpRPnl30"
#     private_key_part13 = "\nZtOkgpUC3pkMHInZFW8Mj3dDzL18km6qFgGAKai4829/S6sSCNSjn42vtQh55WdF"
#     private_key_part14 = "\ndHiQrIjRsWJk6c2OilqILZ0to+1XgTT+7069HkWsBRDPP4cRuQ19YS1DzAxd6H9N"
#     private_key_part15 = "\n4O8TVJZNDpQCVM86pzGrvPmEXQKBgQDVEVbAaazy1O1dFCLTI0oPniY7+noE1QWu"
#     private_key_part16 = "\n7iRL5lBTfJGm/AgVSvtmPfKZAVPBLAq0+zOj5D+BKIZXE7Xmj+PDhjyQSDrI6naX"
#     private_key_part17 = "\nnqbeqGbRwajcuDBZ3NQp1oCNc7UPisXgqV15t8hTGBbrPeyzE2dwclXXytxUj48k"
#     private_key_part18 = "\nv0hyizFAAwKBgCznrOSxbPtH51xPKpkZsXAYKlxfgcJrkh/U8SEpfbDWr9urzRNY"
#     private_key_part19 = "\nzEsNpix84K56RhusgHL8JXljBWm2bHwtwzUGUd+0w8zReJ+XOAt6uuyB2Novy+6R"
#     private_key_part20 = "\nznISzWmzyRlGtXeI+cvbwpGHq0XolMvSdoCDVsYc2y+xwiEPusgjzqjdAoGBAKA3"
#     private_key_part21 = "\nvpVHoa6kYK0KVDmSosFlufiGHDT//psRJigQ0zxEQr5fbLCeRrcWRBO8BMAQnyiC"
#     private_key_part22 = "\ncM1/+CTmVUarYrAyaSIBEg+o0NN+Q5k1yuNJnK+EQbdfpbQdM0kWrGoxpOhAARY0"
#     private_key_part23 = "\nJT8+7JtXVPyl/xSVtcW/pD91owLPRONsF01Sz8EDAoGBALYXqViV6FvfTKrjQG6D"
#     private_key_part24 = "\nchCDghsej8EJqgNfyNJ3M+QXyKAUVXwX1WH78OCqbWzHnuCSQedyFfvVkSrouLDm"
#     private_key_part25 = "\n4Z3PLL22fY1NuOGJp5YPuy7Ohb3CbU4kGp5Y8ne4peFJiZecgQYH54mGkhdTCaZb"
#     private_key_part26 = "\nA9Oo2xQLmTYUfoMegDEUQKIJ\n-----END PRIVATE KEY-----\n"
    


def caesar_encrypt_all(text, shift=4):
    encrypted = ""
    for char in text:
        encrypted += chr((ord(char) + shift) % 256)  # stay within byte range
    return encrypted

def caesar_decrypt_all(text, shift=4):
    decrypted = ""
    for char in text:
        decrypted += chr((ord(char) - shift) % 256)
    return decrypted

# Example usage
private_key_part2 = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC4bbHIOoOmCYKe"

encrypted_text = caesar_encrypt_all(private_key_part2)
decrypted_text = caesar_decrypt_all(encrypted_text)

print("Encrypted:", encrypted_text, "\n")

print("Original :", private_key_part2)
print("Decrypted:", decrypted_text)
