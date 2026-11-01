app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
doc_name = app.activeDocument.name if app.activeDocument else 'none'
print({'action': 'active_design', 'design_name': doc_name,
       'bodies': root.bRepBodies.count})
