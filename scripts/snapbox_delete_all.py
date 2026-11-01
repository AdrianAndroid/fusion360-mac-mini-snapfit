app = adsk.core.Application.get()
root = adsk.fusion.Design.cast(app.activeProduct).rootComponent
names = [b.name for b in root.bRepBodies]
for b in [b for b in root.bRepBodies]:
    b.deleteMe()
print({'deleted': names, 'remaining': root.bRepBodies.count})
