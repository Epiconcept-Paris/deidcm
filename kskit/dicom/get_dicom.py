from pydicom.dataset import Dataset
from pynetdicom import (
    AE, build_role, evt,
    StoragePresentationContexts,
    QueryRetrievePresentationContexts,
    debug_logger
)

from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelGet,
    PatientStudyOnlyQueryRetrieveInformationModelGet,
    PlannedImagingAgentAdministrationSRStorage,
    PerformedImagingAgestAdministrationSRStorage,
    EncapsulatedSTLStorage,
)

storage_dest = ""

# Implement the handler for evt.EVT_C_STORE
def handle_store(event):
    """Handle a C-STORE request event."""
    ds = event.dataset
    ds.file_meta = event.file_meta
    # Save the dataset using the SOP Instance UID as the filename
    ds.save_as(f"{storage_dest}/{ds.SOPInstanceUID}", write_like_original=False)
    #import pdb; pdb.set_trace() 
    # Return a 'Success' status
    return 0x0000

def info_logger():
  """Setup the pynetdicom logging for info."""
  import logging 
  logger = logging.getLogger('pynetdicom')
  # Ensure only have one StreamHandler
  logger.handlers = []
  handler = logging.StreamHandler()
  logger.setLevel(logging.INFO)
  formatter = logging.Formatter('%(levelname).1s: %(message)s')
  handler.setFormatter(formatter)
  logger.addHandler(handler)

def get_dicom(ids, dest, server = "127.0.0.1", port = 11112, title = "ANY", retrieveLevel = 'SERIES'):
  #info_logger()
  handlers = [(evt.EVT_C_STORE, handle_store)]
  global storage_dest 
  storage_dest = dest
  # Initialise the Application Entity
  ae = AE()
  
  
  _exclusion = [
      PlannedImagingAgentAdministrationSRStorage,
      PerformedImagingAgestAdministrationSRStorage,
      EncapsulatedSTLStorage,
  ]
  store_contexts = [
      cx for cx in StoragePresentationContexts
      if cx.abstract_syntax not in _exclusion
  ]
  # Extended Negotiation - SCP/SCU Role Selection
  ext_neg = []
  ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
  ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
  ae.add_requested_context(PatientStudyOnlyQueryRetrieveInformationModelGet)
  for cx in store_contexts:
      ae.add_requested_context(cx.abstract_syntax)
      # Add SCP/SCU Role Selection Negotiation to the extended negotiation
      # We want to act as a Storage SCP
      ext_neg.append(build_role(cx.abstract_syntax, scp_role=True))
  
  
  
  # Create our Identifier (query) dataset
  # We need to supply a Unique Key Attribute for each level above the
  #   Query/Retrieve level
  ds = Dataset()
  ds.QueryRetrieveLevel = retrieveLevel
  if retrieveLevel == "SERIES":
    ds.SeriesInstanceUID = ids
  elif retrieveLevel == "PATIENT":
    ds.PatientID = ids
  elif retrieveLevel == "STUDY":
    ds.StudyInstanceUID = ids
  else:
    raise ValueError("Retrieve level must be one of 'SERIES', 'PATIENT', 'STUDY' but {retrieveLevel} was passed")
     
  # Associate with peer AE at IP 127.0.0.1 and port 11112
  assoc = ae.associate(server, port, ae_title=title, ext_neg=ext_neg, evt_handlers=handlers)
  
  if assoc.is_established:
      # Use the C-GET service to send the identifier
      responses = assoc.send_c_get(ds, PatientRootQueryRetrieveInformationModelGet)
      for (status, identifier) in responses:
          if status:
              #import pdb; pdb.set_trace() 
              if status.NumberOfCompletedSuboperations == 1:
                print (f"{ids} downloaded successfully") 
              elif status.NumberOfCompletedSuboperations == 0:
                print (f"id {ids} not found") 
              else:
                print('C-GET query status: 0x{0:04x}'.format(status.Status))
          else:
              print('Connection timed out, was aborted or received invalid response')
  
      # Release the association
      assoc.release()
  else:
      print('Association rejected, aborted or never connected')
  
#get_dicom(ids='1.3.6.1.4.1.9590.100.1.2.25530538411839768118282182472795553760', dest = "/tmp/pynetdicom", server = "127.0.0.1", port = 11112, title = b'DCM4CHEE')

