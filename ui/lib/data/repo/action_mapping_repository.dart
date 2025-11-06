import 'dart:io';
import 'dart:convert';
import 'package:app/cubits/action_mapping_cubit.dart';
import 'package:flutter/services.dart' show rootBundle;

const String mappingsFileLocation = 'assets/action_mappings.json';

class ActionMappingRepository {
  Future<Map<String, dynamic>> _loadJson() async {
    final jsonString = await rootBundle.loadString(mappingsFileLocation);
    final decoded = jsonDecode(jsonString) as Map<String, dynamic>;

    return decoded.map((actor, actions) {
      final actionMap = (actions as Map<String, dynamic>).map((
        action,
        phrases,
      ) {
        return MapEntry(action, List<String>.from(phrases));
      });
      return MapEntry(actor, actionMap);
    });
  }

  Future<void> _saveJson(Map<String, ActionPhraseMap> data) async {
    final file = File(mappingsFileLocation);
    final encoder = const JsonEncoder.withIndent('  ');
    final prettyString = encoder.convert(data);

    await file.writeAsString(prettyString);
  }

  Future<ActionMapping> read() async {
    final data = await _loadJson();
    ActionMapping actionMapping = {};

    data.forEach((actorName, actionPhraseMap) {
      Actor actor = Actor.values.byName(actorName.split('.').last);
      actionMapping[actor] = actionPhraseMap;
    });

    return actionMapping;
  }

  Future<void> write(ActionMapping mappings) async {
    Map<String, ActionPhraseMap> data = {};

    mappings.forEach((actor, actionPhraseMap) {
      String actorName = actor.toString();
      data[actorName] = actionPhraseMap;
    });

    return await _saveJson(data);
  }
}
