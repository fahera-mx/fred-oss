from fred.settings import get_environ_variable


def test_env_retrieval():
    env_var_not_exists = "ENV_VAR_THAT_DOESNT_EXISTS"
    env_var_default = "default"
    assert not get_environ_variable(name=env_var_not_exists, enforce=False)
    assert get_environ_variable(name=env_var_not_exists, default=env_var_default) == env_var_default
