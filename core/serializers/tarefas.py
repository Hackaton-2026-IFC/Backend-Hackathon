from rest_framework import serializers

from core.models import Projeto, Tarefa
from core.serializers.microtarefas import MicroTarefaSerializer


class TarefaSerializer(serializers.ModelSerializer):
    projeto = serializers.PrimaryKeyRelatedField(queryset=Projeto.objects.all())
    criado_por = serializers.PrimaryKeyRelatedField(read_only=True)
    microtarefas = MicroTarefaSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(choices=Tarefa.STATUS_CHOICES, required=False)
    urgencia = serializers.SerializerMethodField()
    dependencias = serializers.PrimaryKeyRelatedField(queryset=Tarefa.objects.all(), many=True, required=False)

    class Meta:
        model = Tarefa
        fields = [
            'id', 'projeto', 'titulo', 'descricao', 'prioridade', 'status',
            'dependencias', 'responsavel', 'criado_por', 'concluida',
            'data_criacao', 'data_limite', 'prazo_antecipado',
            'urgencia', 'urgencia_manual', 'microtarefas', 'clima_influencia', 'localizacao',
        ]
        read_only_fields = ['id', 'data_criacao', 'criado_por', 'microtarefas']

    def get_urgencia(self, obj):
        return obj.urgencia

    def validate(self, attrs):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError('Autenticação obrigatória.')

        projeto = attrs.get('projeto', getattr(self.instance, 'projeto', None))
        if projeto is None or not projeto.membros.filter(usuario=request.user).exists():
            raise serializers.ValidationError({'projeto': 'Você não participa deste projeto.'})

        depende_clima = attrs.get('clima_influencia', getattr(self.instance, 'clima_influencia', False))
        localizacao = attrs.get('localizacao', getattr(self.instance, 'localizacao', ''))
        if depende_clima and not localizacao.strip():
            raise serializers.ValidationError({'localizacao': 'Informe uma cidade quando o clima influenciar na tarefa.'})
        prazo_oficial = attrs.get('data_limite', getattr(self.instance, 'data_limite', None))
        antecipado = attrs.get('prazo_antecipado', getattr(self.instance, 'prazo_antecipado', None))
        if antecipado and not prazo_oficial:
            raise serializers.ValidationError({'prazo_antecipado': 'Informe o prazo oficial antes do antecipado.'})
        if antecipado and antecipado > prazo_oficial:
            raise serializers.ValidationError({'prazo_antecipado': 'O prazo antecipado não pode ultrapassar o oficial.'})

        responsavel = attrs.get('responsavel', getattr(self.instance, 'responsavel', None))
        if responsavel is not None and not projeto.membros.filter(usuario=responsavel).exists():
            raise serializers.ValidationError({'responsavel': 'O responsável deve participar do projeto.'})

        dependencias = attrs.get('dependencias', list(self.instance.dependencias.all()) if self.instance else [])
        for dependencia in dependencias:
            if dependencia.projeto_id != projeto.pk:
                raise serializers.ValidationError({'dependencias': 'Dependências devem pertencer ao mesmo projeto.'})
            if self.instance and dependencia.pk == self.instance.pk:
                raise serializers.ValidationError({'dependencias': 'Uma tarefa não pode depender de si mesma.'})
            if self.instance:
                visitados, pilha = set(), [dependencia]
                while pilha:
                    atual = pilha.pop()
                    if atual.pk == self.instance.pk:
                        raise serializers.ValidationError({'dependencias': 'Dependência circular detectada.'})
                    if atual.pk in visitados:
                        continue
                    visitados.add(atual.pk)
                    pilha.extend(atual.dependencias.all())

        status = attrs.get('status', getattr(self.instance, 'status', Tarefa.STATUS_PLANEJADO))
        concluida = attrs.get('concluida', getattr(self.instance, 'concluida', False))
        if 'status' in attrs and 'concluida' in attrs and concluida != (status == Tarefa.STATUS_CONCLUIDO):
            raise serializers.ValidationError({'concluida': 'O campo concluida deve corresponder ao status.'})
        if 'concluida' in attrs and 'status' not in attrs:
            status = Tarefa.STATUS_CONCLUIDO if concluida else Tarefa.STATUS_PLANEJADO
            attrs['status'] = status

        if status == Tarefa.STATUS_CONCLUIDO:
            if any(dep.status != Tarefa.STATUS_CONCLUIDO for dep in dependencias):
                raise serializers.ValidationError({'dependencias': 'Todas as tarefas predecessoras devem estar concluídas.'})
            if self.instance and self.instance.microtarefas.exclude(concluida=True).exists():
                raise serializers.ValidationError({'status': 'Conclua todas as microtarefas primeiro.'})

        if self.instance and status != Tarefa.STATUS_CONCLUIDO:
            if self.instance.tarefas_dependentes.filter(status=Tarefa.STATUS_CONCLUIDO).exists():
                raise serializers.ValidationError({'status': 'Reabra as tarefas dependentes antes desta.'})
            if self.instance.microtarefas.filter(concluida=True).exists() and status == Tarefa.STATUS_PLANEJADO:
                raise serializers.ValidationError({'status': 'Uma tarefa com etapas concluídas não pode voltar a planejado.'})
        return attrs

    def create(self, validated_data):
        dependencias = validated_data.pop('dependencias', [])
        status = validated_data.get('status', Tarefa.STATUS_PLANEJADO)
        validated_data['concluida'] = status == Tarefa.STATUS_CONCLUIDO
        tarefa = super().create(validated_data)
        tarefa.dependencias.set(dependencias)
        return tarefa

    def update(self, instance, validated_data):
        dependencias = validated_data.pop('dependencias', None)
        if 'status' in validated_data:
            validated_data['concluida'] = validated_data['status'] == Tarefa.STATUS_CONCLUIDO
        tarefa = super().update(instance, validated_data)
        if dependencias is not None:
            tarefa.dependencias.set(dependencias)
        return tarefa
