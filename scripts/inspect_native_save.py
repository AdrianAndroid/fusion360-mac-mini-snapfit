app = adsk.core.Application.get()
doc = app.activeDocument
print({
    'document_name': doc.name,
    'is_saved': doc.isSaved,
    'save_doc': doc.save.__doc__,
    'save_as_doc': doc.saveAs.__doc__,
})
