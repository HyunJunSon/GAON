#!/usr/bin/env python3
import sys
sys.path.insert(0, '../backend')
from app.core.config import settings

print(f'export TF_VAR_db_user="{settings.db_user}"')
print(f'export TF_VAR_db_password="{settings.db_password}"')
print(f'export TF_VAR_db_name="{settings.db_name}"')
