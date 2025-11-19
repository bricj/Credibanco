La presente guía es referencia para crear agentes de IA con el servicio Amazon Bedrock AgentCore del proveedor de servicios en la nube AWS.

La construcción del agente se realiza a través de un IDE (entorno de desarrollo integrado). Para efectos de la presente guía, se utilizará el IDE VSCode y el lenguaje de programación Python, así mismo, se utilizará el Command Line Interface (CLI) de AWS.

Lo primero que se debe realizar es parametrizar el entorno de desarrollo y habilitar los permisos IAM.

1.	Garantizar tener instalado en la máquina local el lenguaje de programación Python con la herramienta Pip y el IDE VsCode.

https://www.datacamp.com/es/tutorial/setting-up-vscode-python

2.	Se utilizará UV para gestionar las dependencias del proyecto. Se instala de la siguiente manera en la terminal (se recomienda utilizar git bash):

pip install uv

Para validar que uv se ha instalado de forma correcta, validar con el siguiente comando:

	uv --version

3.	Usuarios y políticas de AWS

El usuario raíz de AWS (AWS root user) es la identidad principal y más poderosa de una cuenta de Amazon Web Services. Esta identidad se crea automáticamente cuando abres la cuenta con tu correo electrónico y contraseña de AWS.

Es el usuario dueño de la cuenta. Está asociado directamente al correo electrónico con el que se creó la cuenta de AWS. Tiene acceso total e ilimitado a absolutamente todos los servicios, recursos, configuraciones y aspectos de facturación.

Para la administración diaria se deben crear usuarios o roles IAM con privilegios mínimos necesarios. En este orden de ideas, es necesario crear usuarios para la creación del agente con amazon bedrock agentcore.

3.1 Crear usuario

Para crear un usuario, se accede a través de la consola al servicio IAM con el usuario raíz, en el menú de la izquierda se accede a personas y se indica crear persona

Se especifican los detalles de la persona y click en siguiente

Se establecen permisos a la persona, es posible agregar la persona a grupos existentes, copiar permisos de otras personas o indicar de forma directa las políticas (permisos). Para asignar los permisos, se marcan en la sección “políticas de permisos”

Inicialmente, se recomienda seleccionar los siguientes permisos, no obstante, más adelante se incluirá la política mediante el archivo en formato json.

En el tercer paso se crear la persona. Importante considerar que una vez creada la persona, AWS asigna un link de acceso, usuario y contraseña. Importante guardar el csv con las credenciales (solo se puede descargar una única vez). Así mismo, según las opciones marcada, cuando la persona acceda a su cuenta por primera vez, deberá cambiar la contraseña.


3.2 Crear política
En el menú de la parte izquierda, se indica políticas, luego crear política

Una vez se accede, se da click en json y se habilita el editor de políticas. En el editor se incluye la política que se compartirá

En la segunda sección se indica el nombre de la política y descripción de la misma. Se recomienda llamarla build_agents.

Para asociar la política, se entra a la política, entidades asociadas y se da click en asociar. Allí se indica el usuario o persona.

Así mismo, es posible asignar política al usuario de forma directa. Se accede a persona, se da click sobre la persona y se da click en agregar permisos, opción crear política insertada:

De igual forma que en el anterior paso, se da click en json y se ingresa la política. Se recomienda guardar la política como build_agents_v2

4.	Crear claves de acceso
Para acceder a través de CLI, es necesario que el usuario cuente con claves de acceso. Por ello, en el servicio IAM con el usuario raíz, se accede donde la persona, sección credenciales de seguridad y subsección claves de acceso, se da click en crear clave de acceso.

Posteriomente, se crear la clave de acceso. Se obtendrá una clave de acceso y una clave de acceso secreta. Es relevante indicar la región utilizada.

Importante guardar el archivo exportable dado que no se podrá recuperar dicha información.

5.	Configurar AWS CLI

Para configurar AWS CLI, en la terminal de VSCode se debe instalar la dependencia:

uv tool install awscli

aws --version

ej: aws-cli/1.42.75

aws configure

Se indica la clave de acceso, la clave de acceso secreta, la región y en el último campo, indicar “json”.

Las credenciales crearán un archivo que permitirán la conexión con AWS.

6.	Se crea el directorio:

mkdir agentcore-tutorial

cd agentcore-tutorial

Se crea el ambiente virtual de uv

uv init

uv add bedrock-agentcore-starter-toolkit

Se crea subcarpeta para el agente

mkdir agent_deployment

uv init --bare ./agent_deployment && uv --directory ./agent_deployment add strands-agents bedrock-agentcore strands-agents-tools

¿Por qué dos directorios?

•	Proyecto principal: Contiene tus herramientas de desarrollo (kit inicial, herramientas de prueba) para gestionar y desplegar tus agentes.

•	agent_deployment: Contiene únicamente las dependencias de ejecución de tus agentes, que se empaquetan dentro del contenedor desplegado.

•	Esta separación mantiene tu contenedor de despliegue liviano y seguro, mientras te permite conservar todas tus capacidades de desarrollo.

7.	Crear el archivo tutorial_agent.py

El archivo tutorial_agent.py contiene dos ejemplos, en la primera parte, se debe habilitar la sección: “Production-Ready AI Agent for Amazon Bedrock AgentCore – First Example”

8.	Asignar permisos (política) al agente

A través de IAM con el usuario raíz, se accede a roles, se identifica el agente y se da click en agregar permisos.

Se incluye la política para el agente

9.	Configurar el agente, desplegarlo y evaluarlo.

uv run agentcore configure -e agent_deployment/tutorial_agent.py

uv run agentcore launch

uv run agentcore invoke '{"prompt": "What is 25 * 4 + 10?"}'

uv run agentcore status

Una vez ejecutados los comandos, se cuenta con un agente que tiene la capacidad de realizar cálculos. El repositorio se evidencia de la siguiente manera.

Se incluye la política para el agente

9.	Configurar el agente, desplegarlo y evaluarlo.

uv run agentcore configure -e agent_deployment/tutorial_agent.py

uv run agentcore launch

uv run agentcore invoke '{"prompt": "What is 25 * 4 + 10?"}'

uv run agentcore status

Una vez ejecutados los comandos, se cuenta con un agente que tiene la capacidad de realizar cálculos. El repositorio se evidencia de la siguiente manera.

AgentCore se encarga de crear las imágenes a través de Dockerfile.

10.	Habilitar la segunda parte del código denominado “Production-Ready AI Agent with Memory”

Se ejecuta

uv run agentcore configure -e agent_deployment/tutorial_agent.py

uv run agentcore launch

uv run agentcore status

Definir preferencias en memoria:

uv run agentcore invoke '{"prompt": "Remember that I absolutely love hot tea, especially Earl Grey, and I prefer it with a splash of milk and one sugar"}' --session-id 12345-12345-12345-12345-12345-12345-A --headers "Actor-Id:user123"

sleep 20

Con una sesión diferente, preguntar preferencias:

uv run agentcore invoke '{"prompt": "What kind of hot drinks do I like and how do I prefer them prepared?"}' --session-id 12345-12345-12345-12345-12345-12345-B --headers "Actor-Id:user123"

11.	En el archivo tutorial_agent.py se encuentra un tercer código denominado “Complete Production AI Agent”. 

uv --directory ./agent_deployment add strands-agents-tools[agent_core_code_interpreter]
uv run agentcore configure -e agent_deployment/tutorial_agent.py
uv run agentcore launch
uv run agentcore status

Evaluar escenarios complejos:

uv run agentcore invoke '{"prompt": "My daily tea consumption this week: [3, 5, 4, 6, 2, 4, 7] cups per day. Monday was light, Friday was crazy busy!"}' --session-id 12345-12345-12345-12345-12345-12345-C --headers "Actor-Id:user123"

uv run agentcore invoke '{"prompt": "Calculate the mean, median, and standard deviation of my tea consumption. Create a detailed ASCII bar chart showing daily patterns and provide statistical insights about my consumption trends. Present everything as formatted text - no image files needed."}' --session-id 12345-12345-12345-12345-12345-12345-C --headers "Actor-Id:user123"

12.	Limpiar entorno

uv run agentcore destroy

