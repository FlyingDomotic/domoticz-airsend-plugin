# domoticz-airsend-plugin
 AirSend (https://devmel.com/) Domoticz plug-in

# AirSend Domoticz plugin / Plugin AirSend pour Domoticz

[English version and French version in the same document]

AirSend is a Domoticz Python plugin allowing to send and receive commands to AirSend.

[ Versions françaises et anglaises dans le même document]

AirSend est un plugin Domoticz qui permet de relier des dispositifs AirSend à Domoticz.

## What's for? / A quoi ça sert ?
If you want to send orders to AirSend (https://devmel.com/) devices, this plugin is made for you. In addition, you'll be able to scan frames from one protocol and update Domoticz devices accordingly.

Si vous voulez envoyer des commandes à des unités AirSend (https://devmel.com/), ce plugin est fait pour vous. De plus, vous pourrez écouter les trames d'un protocole,et mettre à jour des dispositifs Domoticz à partir de ces trames.

## Warning / Attention

This plugin is at an early stage, and has only partly be tested, with few Domoticz devices types. In addition, bad JSON configuration files will lead to unexpected behavior. You've been warned!

Ce plugin est en phase de développement initial, et n'a été que partiellement testé, avec seulement certains types de dispositifs Domoticz. De plus, un fichier de configuration JSON incorrect va provoquer des effets inattendus, voire rigolos. Vous avez été prévenus !

## Prerequisites / Prérequis

- Domoticz 2020.0 or higher (but lower version could also work).
- Make sure that your Domoticz supports Python plugins (https://www.domoticz.com/wiki/Using_Python_plugins).
- Make sure AirSend Web Service is installed and running on machine, and has been paired with devices you want to control.
- Should you whish to listen to some protocol, you need to have a local web server with PHP enabled.

- Domoticz 2022.0 ou supérieurs (les versions précédentes peuvent aussi fonctionner).
- Vérifiez que votre version de Domoticz supporte les plugins Python (https://www.domoticz.com/wiki/Using_Python_plugins).
- Assurez-vous que le Web service AirSend est installé et actif sur la machine, et qu'il est appairé avec les unités que vous souhaitez contrôler.
- Si vous souhaitez écouter un protocole, vous devez en plus avoir un werveur web local avec php actif.
## Installation

Follow these steps:

1. Clone repository into your Domoticz plugins folder.
```
cd domoticz/plugins
git clone https://github.com/FlyingDomotic/domoticz-airsend-plugin.git AirSend
```
2. Restart Domoticz.
3. Make sure that "Accept new Hardware Devices" is enabled in Domoticz settings.
4. Go to "Hardware" page and add new item with type "AirSend".
5. Give JSON configuration file name to be used (located in AirSend plugin folder).
6. Export your AirSend configuration and copy configuration.yaml file in AirSend plugin folder.

Thanks to one user, you can find at https://github.com/FlyingDomotic/domoticz-airsend-plugin/issues/2 an exemple of Docker file to install AirSend WebService.

Suivez ces étapes :

1. Clonez le dépôt GitHub dans le répertoire plugins de Domoticz.
```
cd domoticz/plugins
git clone https://github.com/FlyingDomotic/domoticz-airsend-plugin.git AirSend
```
2. Redémarrer Domoticz.
3. Assurez-vous qu' "Acceptez les nouveaux dispositifs" est coché dans les paramètres de Domoticz.
4. Allez dans la page "Matériel" du bouton "configuration" et ajouter une entrée de type "AirSend".
5. Entrez le nom du fichier de configuration JSON à utiliser (qui doit être dans le répertoire d'installation du plugin AirSend).
6. Exportez votre configuration AirSend et copiez le fichier configuration.yaml dans le répertoire d'installation du plugin AirSend.

Grâce à un utilisateur, vous pourrez trouver à https://github.com/FlyingDomotic/domoticz-airsend-plugin/issues/2 un exemple de fichier de configuration Docker pour le service Web AirSend.

## Plugin update / Mise à jour du plugin

1. Go to plugin folder and pull new version :
```
cd domoticz/plugins/AirSend
git pull
```
2. Restart Domoticz.

Note: if you did any changes to plugin files and `git pull` command doesn't work for you anymore, you could stash all local changes using
```
git stash
```

1. Allez dans le répertoire du plugin et charger la nouvelle version :
```
cd domoticz/plugins/AirSend
git pull
```
2. Relancez Domoticz.

Note: si vous avez fait des modifs dans les fichiers du plugin et que la commande `git pull` ne fonctionne pas, vous pouvez écraser les modifications locales avec la commande
```
git stash
```

## Configuration

Plugin uses standard AirSend configuration export file (configuration.yaml) to get description of all AirSend devices. You should copy it in AirSend's plugin folder.
In addition, plugin uses an external JSON configuration file to set installation specific parameters. Here's an example of syntax:

Ce pluging utilise le fichier standard AirSend de configuration (configuration.yaml). Vous devez le copier dans le répertoire du plugin AirSend.
De plus, il utilise un fichier de configuration externe au format JSON pour définir les paramètres spécifiques de l'installation. Voici un exemple de syntaxe :
```ts
{
	"parameters": {
		"domoticzRootUrl": "http://127.0.0.1:8080/",
		"yamlConfigurationFile": "configuration.yaml",
		"webServerFolder": "/var/www/html/",
		"webServerUrl": "http://127.0.0.1/",
		"webServiceUrl": "http://127.0.0.1:33863/",
		"protocolToListen" : 12345,
		"authorization" : "sp://xxxxxxxxxxxxxxxx@xxx.xxx.xxx.xxx?gw=0"
	},
	"mapping": [
		{"Additional remote": {"remoteId": 11111, "remoteSource": 22222, "deviceId": 33333, "deviceSource": 44444},
	]
}
```

Let's see how this is constructed: / Voyons comment c'est construit :

```ts
"domoticzRootUrl": "http://127.0.0.1:8080/",
```

Specify Domoticz root URL. Could include username/password if required.
Donne l'adresse URL de base de Domoticz. Peut inclure également un utilisateur/mot de passe si besoin.

```ts
"yamlConfigurationFile": "configuration.yaml",
```
Specify AirSend configuration YAML file (would you change it).
Donne le nom du fichier de configuration AirSend au format YAML.

```ts
"webServiceUrl": "http://127.0.0.1:33863/",
```
Specify AirSend web service URL to use.
Donne l'adresse du web service AirSpend à utiliser.

```ts
"authorization" : "sp://xxxxxxxxxxxxxxxx@xxx.xxx.xxx.xxx?gw=0"
```
Specify authorization data to use (in AirSend format).
Donne l'authentification à utiliser, au format AirSend.

```ts
"protocolToListen" : 12345,
```
Specify protocol id to listen to. Optionnal. See AirSend documentation to find it.
Donne le numéro de protocole à écouter. Voir les valeurs dans la documentation AirSend.

```ts
"webServerFolder": "/var/www/html/",
```
Specify local web server folder where the callback php file should be copied. Required only if 'protocolToListen' specified.
Donne le nom du répertoire local du serveur web où le fichier de rappel php doit être copié. Requis uniquement si 'protocolToListen' est donné.

```ts
"webServerUrl": "http://127.0.0.1/",
```
Specify local web server address to use to call callback. Can contain sub-folder if callback not at root. Required only if 'protocolToListen' specified.
Donne l'adresse du serveur web local à utiliser pour accéder au rappel. Peut contenir un sous-répertoire si le fichier de rappel n'est pas à la racine. Requis uniquement si 'protocolToListen' est donné.

```ts
{"Additional remote": {"remoteId": 11111, "remoteSource": 22222, "deviceId": 33333, "deviceSource": 44444}
```

Should you listen to one protocol and have multiple remote commands for the same device (including AirSend itself in case of protocol with sequence numbers), you can specify here additiona remote id and source. Remote represents the addition remote, device is AirSend device in configuration.yaml. 'remoteId' and 'deviceId' should probably be the same. Add one line per remote.

Si vous écoutez un protocole et avez plusieurs télécommandes pour une même unité (inclant AirSend lui-même dans le cas de protocoles avec compteurs), vous pouvez donner ici l'id et la source de la télécommande additionnelle. Remote correspond à la télécommande additionnelle, device est l'unité dans le fichier configuration.yaml. 'remoteId' et 'deviceId' devrait probablement être identiques. Ajouter une ligne par télécommande additionnelle.

## Architecture details / Détails sur l'architecture

As per AirSend's documentation, AirSend box is able to do two things:
1. Send command "blindly" in the air,
2. Optionnaly listen to one (and only one) protocol. This protocol could be `0`, with a special meaning of `generic 433 protocol`.

Should you wish only blindly send commands, don't specify `protoclToListen` in AirSend.json file, and that's it. `webServerUrl`, `webServerFolder` and `mapping` are useless, and no callback willl be used. Note in that case that Domoticz devices would normally be push button, as no feedback is received, nor remote device frames received.

If you enable one protocol listening, then `webServerFolder` and `webServerUrl` are required, to determine where to copy callback in the right folder and to call it.

Callback will be called by AirSend web service, and captured frame sent to Domoticz, which in turn will send it to the AirSend plug-in.

Captured frames will depend on received, remote and AirSend box configuration. This could be remote key press, received order confirmation and/or remote status. Due to diversity of devices, o²nly tests could determine exactly what kind of frames can be received. In this case, having full debug and webservice log may help (see under).

Selon la documentation AirSend, le boitier AirSend est capable de faire 2 choses :
1. Envoyer à l'aveugle des commandes radio
2. Facultativement écouter un protocole (et seulement un). Ce protocole peut être le protpcole `0`, nommé `protocole 433 générique`.

Si vous ne souhaitez qu'envoyer des commandes à l'aveugle, ne spécifiez pas `protocolToListen` dans le fichier Airsend.json, et voilà ! `webServerUrl`, `webServerFolder` et `mapping` sont inutiles, et on n'utilisera pas de callback. Noter que dans ce cas, les dispositifs Domoticz devrait être du type bouton poussoir, car aucune retour ni message de télécommande n'est reçu.

Si vous définissez un protocole à écouter, `webServerFolder` et `webServerUrl` sont requis pour déterminer où copier le callback et comment l'apppeller.

Le callback sera utilisé par le web service AirSend pour envoyer les trames reçues à Domoticz, qui les enverra au plug-in AirSend.

LEs trames capturées dépendent du récepteur, de la télécommande et du paramétrage du boitier AirSend. Celà peut être l'appui sur une télécommande, la confirmation d'un ordre ou un état distant. Etant donné la diversité des appareils, seuls des tests permettent de savoir avec précision les trames qui sont reçues. Avoir défini une trace complète et avoir accès au log du web service peuvent aider (voir plus bas).

## Supported AirSend device type and command / Types d'unités AisSend et commandes supportées

Here's the list of AirSend devices type and commands currently supported:

| Type | Usage               | Commands              |
|------|---------------------|-----------------------|
| 4098 | Boutton             | Toggle                |
| 4097 | Switch              | On/Off                |
| 4098 | Cover               | Up/Down/Stop          |
| 4099 | Cover with position | Up/Down/Stop/Position |

Voici la liste des unités AirSend et des commandes supportées :

| Type | Usage               | Commands              |
|------|---------------------|-----------------------|
| 4098 | Bouton              | Toggle                |
| 4097 | Interrupteur        | On/Off                |
| 4098 | Volet               | Up/Down/Stop          |
| 4099 | Volet avec position | Up/Down/Stop/Position |

## Debuging plug-in / Déverminage du plug-in

If something don't work as expected/required, it could be a good idea to modify debug log level from `Normal` to `Extra verbose` before restarting plug-in (to restart plug-in, either restart Domoticz or click on `Modify` when plug-in is selected in `Hardware` tab of `Configuration`).

In addition, an extract of web service log (AirSendWebService.log in web service folder) may help.

Si quelque chose ne fonctionne pas comme documenté/souhaité, il peut être habile de passer le niveau de log du plug-in de `Normal` à `Extra verbose` avant de relancer le plug-in (pour relancer le plug-in, vous pouvez soit relancer Domoticz, soit cliquer sur "Modifier" lorsque le plug-in est sélectionné dans l'onglet `Matériel` du menu `Configuration`.

De plus, un extrait du log du web service (AirSendWebService.log dans le répertoire du web service) peut aider.