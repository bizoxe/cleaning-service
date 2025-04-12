"""
Initialisation of user roles.
Creating an administrator and editor in the database.
"""

import typer
from sqlalchemy import select

from api.api_v1.users.models import (
    Permission,
    Role,
    User,
)
from auth.utils.auth_utils import hash_password
from core.config import settings
from core.models import db_helper
from crud.users import users_crud

ADMIN_EMAIL = settings.roles.admin_email
ADMIN_PWD = settings.roles.admin_pwd
EDITOR_EMAIL = settings.roles.editor_email
EDITOR_PWD = settings.roles.editor_pwd

async_session = db_helper.get_ctx_async_session


async def seed_roles_and_permissions() -> None:
    user_role = Role(id=1, name="UserAuth")
    editor_role = Role(id=2, name="Editor")
    admin_role = Role(id=3, name="Admin")
    user_customer_role = Role(id=4, name="UserAuthCustomer")
    user_cleaner_role = Role(id=5, name="UserAuthCleaner")

    read_permission = Permission(name="read")
    modify_permission = Permission(name="modify")
    write_permission = Permission(name="write")
    delete_permission = Permission(name="delete")
    customer = Permission(name="customer")
    cleaner = Permission(name="cleaner")

    admin_role.permissions.extend([write_permission, delete_permission])
    editor_role.permissions.extend([write_permission])
    user_role.permissions.extend([read_permission, modify_permission])
    user_customer_role.permissions.extend([read_permission, modify_permission, customer])
    user_cleaner_role.permissions.extend([read_permission, modify_permission, cleaner])
    async with async_session() as session:
        result = await session.execute(select(Role))
        roles_already_created = result.scalars().all()
        if not roles_already_created:
            session.add_all([user_role, editor_role, admin_role, customer, cleaner])
            await session.commit()
            success_msg = typer.style(
                "Roles: authenticated user, editor, administrator, customer, cleaner successfully created",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(message=success_msg, color=True)

        else:
            warn_msg = typer.style(
                "Roles have already been created in the database",
                fg=typer.colors.YELLOW,
                bold=True,
            )
            typer.echo(message=warn_msg, color=True)


async def create_admin_and_editor() -> None:
    admin_data = {
        "email": ADMIN_EMAIL,
        "email_verified": True,
        "password": hash_password(plaintext_password=ADMIN_PWD),
        "is_active": True,
        "profile_exists": True,
        "role_id": 3,
    }
    editor_data = {
        "email": EDITOR_EMAIL,
        "email_verified": True,
        "password": hash_password(plaintext_password=EDITOR_PWD),
        "is_active": True,
        "profile_exists": True,
        "role_id": 2,
    }
    async with async_session() as session:
        admin = await users_crud.get_user_by_email(session=session, email=ADMIN_EMAIL)
        editor = await users_crud.get_user_by_email(session=session, email=EDITOR_EMAIL)
        if admin is None:
            admin_register = User(**admin_data)
            session.add(admin_register)
            await session.commit()
            await session.refresh(admin_register)
            success_msg_adm = typer.style(
                text=f"An administrator with the email ‘{admin_register.email}’ has been created",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(message=success_msg_adm, color=True)

            if editor is None:
                editor_register = User(**editor_data)
                session.add(editor_register)
                await session.commit()
                await session.refresh(editor_register)
                success_msg_editor = typer.style(
                    text=f"An editor with the email ‘{editor_register.email}’ has been created",
                    fg=typer.colors.GREEN,
                    bold=True,
                )
                typer.echo(message=success_msg_editor, color=True)
        else:
            if admin:
                warn_msg_adm = typer.style(
                    text=f"An administrator with email ‘{admin.email}’ already exists in the database",
                    fg=typer.colors.YELLOW,
                    bold=True,
                )
                typer.echo(message=warn_msg_adm, color=True)
            if editor:
                warn_msg_editor = typer.style(
                    text=f"An editor with email '{editor.email}' already exists in the database",
                    fg=typer.colors.YELLOW,
                    bold=True,
                )
                typer.echo(message=warn_msg_editor, color=True)
