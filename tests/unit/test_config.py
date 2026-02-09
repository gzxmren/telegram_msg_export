import pytest
import os
import yaml
from app.config import AppConfig, TaskModel, ExporterSettings

def test_task_model_validation():
    data = {
        "name": "Test Task",
        "sources": 123456,  # Single value should be normalized to list
        "output": {"path": "./test.csv", "format": "csv"}
    }
    task = TaskModel(**data)
    assert task.name == "Test Task"
    assert task.sources == [123456]
    assert task.output.path == "./test.csv"

def test_config_load_non_existent():
    # Reset state
    AppConfig._last_mtime = 0
    result = AppConfig.load("non_existent.yaml")
    assert result is False

def test_config_load_valid(tmp_path):
    config_file = tmp_path / "config.yaml"
    content = {
        "settings": {"loop_interval": 600},
        "tasks": [
            {
                "name": "Task 1",
                "sources": ["all"],
                "output": {"path": "out.csv"}
            }
        ]
    }
    with open(config_file, "w") as f:
        yaml.dump(content, f)
    
    # Reset state to force load
    AppConfig._last_mtime = 0
    result = AppConfig.load(str(config_file))
    
    assert result is True
    assert AppConfig.settings.loop_interval == 600
    assert len(AppConfig.tasks) == 1
    assert AppConfig.tasks[0].name == "Task 1"
