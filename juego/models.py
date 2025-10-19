# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class Alumno(models.Model):
    idalumno = models.IntegerField(db_column='idAlumno', primary_key=True)  # Field name made lowercase.
    profesor_idprofesor = models.ForeignKey('Profesor', models.DO_NOTHING, db_column='profesor_idProfesor')  # Field name made lowercase.
    emailalumno = models.CharField(db_column='emailAlumno', max_length=100, blank=True, null=True)  # Field name made lowercase.
    nombrealumno = models.CharField(db_column='nombreAlumno', max_length=200, blank=True, null=True)  # Field name made lowercase.
    carreraalumno = models.CharField(db_column='carreraAlumno', max_length=100, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'alumno'


class Desafio(models.Model):
    iddesafio = models.IntegerField(db_column='idDesafio', primary_key=True)  # Field name made lowercase.
    idadministrador_idadministrador = models.ForeignKey('Idadministrador', models.DO_NOTHING, db_column='idadministrador_idAdministrador')  # Field name made lowercase.
    nombredesafio = models.CharField(db_column='nombreDesafio', max_length=100, blank=True, null=True)  # Field name made lowercase.
    tokensdesafio = models.IntegerField(db_column='tokensDesafio', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'desafio'


class Desafiolego(models.Model):
    iddesafiolego = models.IntegerField(db_column='idDesafioLego', primary_key=True)  # Field name made lowercase.
    reto_idreto = models.ForeignKey('Reto', models.DO_NOTHING, db_column='reto_idReto')  # Field name made lowercase.
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'desafiolego'


class Encuesta(models.Model):
    idencuesta = models.IntegerField(db_column='idEncuesta', primary_key=True)  # Field name made lowercase.
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')  # Field name made lowercase.
    fecha = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'encuesta'


class Evaluacion(models.Model):
    idevaluacion = models.IntegerField(db_column='idEvaluacion', primary_key=True)  # Field name made lowercase.
    desafiolego_iddesafiolego = models.ForeignKey(Desafiolego, models.DO_NOTHING, db_column='desafioLego_idDesafioLego')  # Field name made lowercase.
    puntaje = models.IntegerField(blank=True, null=True)
    grupoevaluado = models.IntegerField(db_column='grupoEvaluado', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'evaluacion'


class Grupo(models.Model):
    idgrupo = models.IntegerField(db_column='idGrupo', primary_key=True)  # Field name made lowercase.
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')  # Field name made lowercase.
    tokens = models.IntegerField(blank=True, null=True)
    etapa = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'grupo'


class Idadministrador(models.Model):
    idadministrador = models.IntegerField(db_column='idAdministrador', primary_key=True)  # Field name made lowercase.
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')  # Field name made lowercase.
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'idadministrador'


class Mapaempatia(models.Model):
    idmapaempatia = models.IntegerField(db_column='idMapaEmpatia', primary_key=True)  # Field name made lowercase.
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio')  # Field name made lowercase.
    emociones = models.CharField(max_length=200, blank=True, null=True)
    gustos = models.CharField(max_length=200, blank=True, null=True)
    entorno = models.CharField(max_length=200, blank=True, null=True)
    necesidades = models.CharField(max_length=200, blank=True, null=True)
    limitaciones = models.CharField(max_length=200, blank=True, null=True)
    motivaciones = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mapaempatia'


class Profesor(models.Model):
    idprofesor = models.IntegerField(db_column='idProfesor', primary_key=True)  # Field name made lowercase.
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')  # Field name made lowercase.
    emailprofesor = models.CharField(max_length=100, blank=True, null=True)
    facultad = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profesor'


class Reto(models.Model):
    idreto = models.IntegerField(db_column='idReto', primary_key=True)  # Field name made lowercase.
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio')  # Field name made lowercase.
    nombrereto = models.CharField(db_column='nombreReto', max_length=90, blank=True, null=True)  # Field name made lowercase.
    descripcionreto = models.CharField(db_column='descripcionReto', max_length=200, blank=True, null=True)  # Field name made lowercase.
    recompensareto = models.CharField(db_column='recompensaReto', max_length=100, blank=True, null=True)  # Field name made lowercase.
    costoreto = models.CharField(db_column='costoReto', max_length=90, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'reto'


class Tokens(models.Model):
    idtokens = models.IntegerField(db_column='idTokens', primary_key=True)  # Field name made lowercase.
    grupo_idgrupo = models.ForeignKey(Grupo, models.DO_NOTHING, db_column='grupo_idGrupo')  # Field name made lowercase.
    numtokens = models.IntegerField(db_column='numTokens', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tokens'


class Usuario(models.Model):
    idusuario = models.IntegerField(db_column='idUsuario', primary_key=True)  # Field name made lowercase.
    password = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuario'