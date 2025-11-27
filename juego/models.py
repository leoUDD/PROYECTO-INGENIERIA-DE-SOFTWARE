from django.db import models


class Alumno(models.Model):
    idalumno = models.AutoField(db_column='idAlumno', primary_key=True)
    profesor_idprofesor = models.ForeignKey('Profesor', models.DO_NOTHING, db_column='profesor_idProfesor')
    emailalumno = models.CharField(db_column='emailAlumno', max_length=100, blank=True, null=True)
    rutalumno = models.CharField(db_column='rutAlumno', max_length=100, blank=True, null=True)
    nombrealumno = models.CharField(db_column='nombreAlumno', max_length=200, blank=True, null=True)
    apellidopaternoalumno = models.CharField(db_column='apellidoPaternoAlumno', max_length=100, blank=True, null=True)
    apellidomaternoalumno = models.CharField(db_column='apellidoMaternoAlumno', max_length=100, blank=True, null=True)
    carreraalumno = models.CharField(db_column='carreraAlumno', max_length=100, blank=True, null=True)
    grupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo', null=True, blank=True)
    class Meta:
        db_table = 'alumno'


class Desafio(models.Model):
    iddesafio = models.AutoField(db_column='idDesafio', primary_key=True)
    idadministrador_idadministrador = models.ForeignKey('Idadministrador', models.DO_NOTHING, db_column='idadministrador_idAdministrador')
    nombredesafio = models.CharField(db_column='nombreDesafio', max_length=100, blank=True, null=True)
    tokensdesafio = models.IntegerField(db_column='tokensDesafio', blank=True, null=True)
    descripciondesafio = models.CharField(db_column='descripcionDesafio', max_length=300, blank=True, null=True)

    class Meta:
        db_table = 'desafio'


class Desafiolego(models.Model):
    iddesafiolego = models.AutoField(db_column='idDesafioLego', primary_key=True)
    reto_idreto = models.ForeignKey('Reto', models.DO_NOTHING, db_column='reto_idReto')
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')

    class Meta:
        db_table = 'desafiolego'


class Encuesta(models.Model):
    idencuesta = models.AutoField(db_column='idEncuesta', primary_key=True)
    grupo_idgrupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='grupo_idGrupo')
    fecha = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'encuesta'


class Evaluacion(models.Model):
    idevaluacion = models.AutoField(db_column='idEvaluacion', primary_key=True)
    desafiolego_iddesafiolego = models.ForeignKey(Desafiolego, models.DO_NOTHING, db_column='desafioLego_idDesafioLego')
    puntaje = models.IntegerField(blank=True, null=True)
    grupoevaluado = models.IntegerField(db_column='grupoEvaluado', blank=True, null=True)

    class Meta:
        db_table = 'evaluacion'


class Grupo(models.Model):
    idgrupo = models.AutoField(db_column='idGrupo', primary_key=True)
    usuario_idusuario = models.ForeignKey('Usuario',models.DO_NOTHING,db_column='usuario_idUsuario',null=True,blank=True)
    tokensgrupo = models.IntegerField(blank=True, null=True, default=12)  # 👈 valor inicial
    etapa = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'grupo'

    # 🪙 método auxiliar para modificar tokens
    def ajustar_tokens(self, cantidad):
        """Suma o resta tokens del grupo."""
        if self.tokensgrupo is None:
            self.tokensgrupo = 0
        self.tokensgrupo += cantidad
        if self.tokensgrupo < 0:
            self.tokensgrupo = 0  # evita números negativos
        self.save()


class Idadministrador(models.Model):
    idadministrador = models.AutoField(db_column='idAdministrador', primary_key=True)
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'idadministrador'


class Mapaempatia(models.Model):
    idmapaempatia = models.AutoField(db_column='idMapaEmpatia', primary_key=True)
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio')
    emociones = models.CharField(max_length=200, blank=True, null=True)
    gustos = models.CharField(max_length=200, blank=True, null=True)
    entorno = models.CharField(max_length=200, blank=True, null=True)
    necesidades = models.CharField(max_length=200, blank=True, null=True)
    limitaciones = models.CharField(max_length=200, blank=True, null=True)
    motivaciones = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'mapaempatia'


class Profesor(models.Model):
    idprofesor = models.AutoField(db_column='idProfesor', primary_key=True)
    usuario_idusuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='usuario_idUsuario')
    emailprofesor = models.CharField(max_length=100, blank=True, null=True)
    facultad = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'profesor'


class Reto(models.Model):
    idreto = models.AutoField(db_column='idReto', primary_key=True)
    desafio_iddesafio = models.ForeignKey(Desafio, models.DO_NOTHING, db_column='desafio_idDesafio')
    nombrereto = models.CharField(db_column='nombreReto', max_length=90, blank=True, null=True)
    descripcionreto = models.CharField(db_column='descripcionReto', max_length=200, blank=True, null=True)
    recompensareto = models.CharField(db_column='recompensaReto', max_length=100, blank=True, null=True)
    costoreto = models.IntegerField(db_column='costoReto', blank=True, null=True)  # 👈 cambio a Integer

    class Meta:
        db_table = 'reto'


class Tokens(models.Model):
    idtokens = models.AutoField(db_column='idTokens', primary_key=True)
    grupo_idgrupo = models.ForeignKey(Grupo, models.DO_NOTHING, db_column='grupo_idGrupo')
    numtokens = models.IntegerField(db_column='numTokens', blank=True, null=True)

    class Meta:
        db_table = 'tokens'


class Usuario(models.Model):
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)
    password = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        db_table = 'usuario'


