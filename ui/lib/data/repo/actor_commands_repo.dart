import 'dart:convert';
import 'dart:io';
import 'package:app/data/actor_commands.dart';
import 'package:flutter/services.dart';

class ActorCommandsRepo {
  final String fileLocation;

  ActorCommandsRepo({required this.fileLocation});

  Future<Map<String, dynamic>> _loadJson() async {
    final jsonString = await rootBundle.loadString(fileLocation);
    return jsonDecode(jsonString) as Map<String, dynamic>;
  }

  Future<void> _saveJson(Map<String, dynamic> data) async {
    final file = File(fileLocation);
    final encoder = const JsonEncoder.withIndent('  ');
    final prettyString = encoder.convert(data);
    await file.writeAsString(prettyString);
  }

  Map<String, dynamic> toDomain(CommandConfig config) {
    return {
      'last_modified': config.lastModified.toIso8601String(),
      'commands': config.commands.map((actorCmds) {
        return {
          'actor': actorCmds.actor.index,
          'commands': actorCmds.commands.map((cmd) {
            return {
              'action': cmd.action.index,
              'reply': cmd.reply,
              'phrases': cmd.phrases,
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
              commands: (actorCmds['commands'] as List)
                  .map(
                    (cmd) => Command(
                      action: Action.values[cmd['action'] as int],
                      reply: cmd['reply'],
                      phrases: List<String>.from(cmd['phrases']),
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
