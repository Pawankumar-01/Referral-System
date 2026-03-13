# from sqlalchemy.orm import Session
# from app.models.notification import Notification, NotificationType, NotificationStatus
# from app.models.patient import Patient
# from app.services.whatsapp_service import send_whatsapp_message
# import uuid


# def create_notification(
#     db: Session,
#     patient_id: str,
#     message: str,
#     notification_type: NotificationType = NotificationType.sms,
# ):

#     notification = Notification(
#         id=str(uuid.uuid4()),
#         patient_id=patient_id,
#         message=message,
#         notification_type=notification_type,
#         status=NotificationStatus.pending,
#     )

#     db.add(notification)

#     patient = db.query(Patient).filter(Patient.id == patient_id).first()

#     if patient and patient.phone:
#         success = send_whatsapp_message(patient.phone, message)

#         if success:
#             notification.status = NotificationStatus.sent
#         else:
#             notification.status = NotificationStatus.failed

#     return notification