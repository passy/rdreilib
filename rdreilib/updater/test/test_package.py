import package, meta

m = meta.Meta("test/update_1.conf")
p = package.Package(m)

m.check()
p.check()
print "Done!"
