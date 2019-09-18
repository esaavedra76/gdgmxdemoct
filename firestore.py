import logging
from firebase_admin import auth, firestore


def initializeBatch():
    return firestore.client().batch()


def commitBatch(batch):
    batch.commit()


def setMatrixCellBatched(batch, cell_id, cell_data):
    doc_ref = firestore.client().collection('matrix').document(cell_id)
    try:
        batch.set(doc_ref, cell_data)
        return True
    except:
        logging.error("unable to set/update document {}".format(cell_id))
        return False


def updateMatrixCellBatched(batch, cell_id, cell_data):
    doc_ref = firestore.client().collection('matrix').document(cell_id)
    try:
        batch.update(doc_ref, cell_data)
        return True
    except:
        logging.error("unable to set/update document {}".format(cell_id))
        return False


def updateMatrixCell(cell_id, cell_data):
    doc_ref = firestore.client().collection('matrix').document(cell_id)
    try:
        doc_ref.update(cell_data)
        return True
    except:
        logging.error("unable to set/update document {}".format(cell_id))
        return False


def getMatrixAll():
    query_ref = firestore.client().collection('matrix')
    try:
        return [el.to_dict() for el in query_ref.get()]
    except:
        logging.error("document(s) not found")
        return None


def getMatrix(row):
    query_ref = firestore.client().collection('matrix').where(u'row', u'==', row)
    try:
        return [el.to_dict() for el in query_ref.get()]
    except:
        logging.error("document(s) not found")
        return None


