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
      'lastModified': config.lastModified.toIso8601String(),
      'commands': config.commands.map((actorCmds) {
        return {
          'actor': actorCmds.actor.name,
          'commands': actorCmds.commands.map((cmd) {
            return {
              'action': cmd.action.name,
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
      lastModified: DateTime.parse(data['lastModified'] as String),
      commands: (data['commands'] as List)
          .map(
            (actorCmds) => ActorCommands(
              actor: Actor.values.firstWhere(
                (a) => a.name == actorCmds['actor'],
              ),
              commands: (actorCmds['commands'] as List)
                  .map(
                    (cmd) => Command(
                      action: Action.values.firstWhere(
                        (a) => a.name == cmd['action'],
                      ),
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
    data['lastModified'] = DateTime.now().toIso8601String();
    await _saveJson(data);
  }
}
