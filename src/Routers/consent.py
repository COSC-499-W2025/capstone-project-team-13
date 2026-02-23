from fastapi import APIRouter

from src.Databases.database import db_manager
from src.Databases.user_config import ConfigManager

router = APIRouter(prefix="/consent", tags=["Consent"])

config_manager = ConfigManager(db_manager)


@router.post("/basic-consent-grant")
def grant_basic_consent():
	config = config_manager.grant_basic_consent()
	return config.to_dict()


@router.post("/basic-consent-revoke")
def revoke_basic_consent():
	config = config_manager.revoke_basic_consent()
	return config.to_dict()


@router.post("/ai-consent-grant")
def grant_ai_consent():
	config = config_manager.grant_ai_consent()
	return config.to_dict()


@router.post("/ai-consent-revoke")
def revoke_ai_consent():
	config = config_manager.revoke_ai_consent()
	return config.to_dict()


@router.get("/basic-consent-status")
def get_basic_consent_status():
	config = config_manager.get_or_create_config()
	return {
		"basic_consent_granted": config.basic_consent_granted,
		"basic_consent_timestamp": config.basic_consent_timestamp.isoformat()
		if config.basic_consent_timestamp
		else None,
	}


@router.get("/ai-consent-status")
def get_ai_consent_status():
	config = config_manager.get_or_create_config()
	return {
		"ai_consent_granted": config.ai_consent_granted,
		"ai_consent_timestamp": config.ai_consent_timestamp.isoformat()
		if config.ai_consent_timestamp
		else None,
	}