"""Tests only fail-closed paths using a fake gh. No remote requests or writes."""
import os
import shutil
import subprocess
from pathlib import Path

def fixture_tree(tmp_path, gh_body):
    scripts=tmp_path/'scripts';scripts.mkdir()
    target=scripts/'publish_github.sh'
    shutil.copy(Path(__file__).parents[1]/'scripts/publish_github.sh',target)
    binpath=tmp_path/'bin';binpath.mkdir()
    gh=binpath/'gh';gh.write_text('#!/bin/bash\n'+gh_body+'\n');gh.chmod(0o700)
    env={**os.environ,'PATH':str(binpath)+os.pathsep+os.environ['PATH']}
    return target,env

def test_rejects_invalid_name(tmp_path):
    path,env=fixture_tree(tmp_path,'echo MUST_NOT_EXECUTE; exit 99')
    result=subprocess.run(['bash',str(path),'../escape'],env=env,capture_output=True,text=True)
    assert result.returncode!=0 and 'Invalid repository name' in result.stderr
    assert 'MUST_NOT_EXECUTE' not in result.stdout

def test_rejects_wrong_account(tmp_path):
    path,env=fixture_tree(tmp_path,'if [[ "$1 $2" == "auth status" ]]; then exit 0; fi\nif [[ "$1 $2" == "api user" ]]; then echo other-account; exit 0; fi\nexit 99')
    result=subprocess.run(['bash',str(path)],env=env,capture_output=True,text=True)
    assert result.returncode!=0 and 'Expected account' in result.stderr
    assert not (tmp_path/'.git').exists()

def test_rejects_existing_repository(tmp_path):
    path,env=fixture_tree(tmp_path,'if [[ "$1 $2" == "auth status" ]]; then exit 0; fi\nif [[ "$1 $2" == "api user" ]]; then echo zhu607705-coder; exit 0; fi\nif [[ "$1 $2" == "repo view" ]]; then exit 0; fi\nexit 99')
    result=subprocess.run(['bash',str(path)],env=env,capture_output=True,text=True)
    assert result.returncode!=0 and 'Repository exists' in result.stderr
    assert not (tmp_path/'.git').exists()

def test_rejects_missing_login(tmp_path):
    path,env=fixture_tree(tmp_path,'exit 1')
    result=subprocess.run(['bash',str(path)],env=env,capture_output=True,text=True)
    assert result.returncode!=0 and 'gh auth login' in result.stderr
