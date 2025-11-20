import 'dart:convert';
import 'dart:io';
import 'package:app/data/actor_commands.dart';
import 'package:path/path.dart' as p;

const String fileName = 'actor_commands.json';

class ActorCommandsRepo {
  late final String fileLocation;

  ActorCommandsRepo() {
    final base = Platform.environment['LOCALAPPDATA']!;
    final folder = p.join(base, 'cgt_ace');
    Directory(folder).createSync(recursive: true);
    fileLocation = p.join(folder, fileName);
  }

  Future<void> _saveJson(Map<String, dynamic> data) async {
    final file = File(fileLocation);

    if (!await file.exists()) {
      await file.create(recursive: true);
    }

    final encoder = const JsonEncoder.withIndent('  ');
    final prettyString = encoder.convert(data);

    await file.writeAsString(prettyString);
  }

  Future<Map<String, dynamic>> _loadJson() async {
    final file = File(fileLocation);

    if (!await file.exists()) {
      await _saveJson(toDomain(CommandConfig.initial()));
      return _loadJson();
    }

    final jsonString = await file.readAsString();
    return jsonDecode(jsonString) as Map<String, dynamic>;
  }

  Map<String, dynamic> toDomain(CommandConfig config) {
    return {
      'last_modified': config.lastModified.toIso8601String(),
      'commands': config.commands.map((actorCmds) {
        return {
          'actor': actorCmds.actor.index,
          'voice': actorCmds.voice.index,
          'commands': actorCmds.commands.map((cmd) {
            return {
              'action': cmd.action.index,
              'reply': cmd.reply,
              'label': cmd.label,
            };
          }).toList(),
        };
      }).toList(),
    };
  }

  CommandConfig fromDomain(Map<String, dynamic> data) {
    return CommandConfig(
      lastModified: DateTime.parse(data['last_modified'] as String),
      commands: (data['commands'] as List)
          .map(
            (actorCmds) => ActorCommands(
              actor: Actor.values[actorCmds['actor'] as int],
              voice: Voice.values[actorCmds['voice'] as int],
              commands: (actorCmds['commands'] as List)
                  .map(
                    (cmd) => Command(
                      action: Action.values[cmd['action'] as int],
                      reply: cmd['reply'],
                      label: cmd['label'],
                    ),
                  )
                  .toList(),
            ),
          )
          .toList(),
    );
  }

  Future<CommandConfig> load() async {
    final data = await _loadJson();
    return fromDomain(data);
  }

  Future<void> save(CommandConfig config) async {
    final data = toDomain(config);
    data['last_modified'] = DateTime.now().toIso8601String();
    await _saveJson(data);
  }
}
