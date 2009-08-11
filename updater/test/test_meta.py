# Not familiar with nose and co yet, so this is just written down and has to be
# reformatted.

from meta import Meta

mdata = Meta("test/update_1.conf")

print mdata._build_validation_hash()
