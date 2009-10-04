from thirdparty.gnupg import GPG

gpg = GPG(gnupghome='/home/pascal/.gnupg', verbose=True)

signature = """iEYEABECAAYFAkqC8hAACgkQC3jHPr+io7BxDwCfVLOOG+I1j3E+FJwO3I5Nka+V
kroAn2tAFmbxaPDT2n5K9FyJMbuS4lcL
=HzNp"""

tar = 'test/test.tar.lzma'

result = gpg.verify_detached(tar, signature)
