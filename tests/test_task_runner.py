from runtime.task_runner import TaskRunner


def test_task_runner_returns_success_result():
    runner = TaskRunner(max_workers=1)
    values = []
    try:
        future = runner.submit(lambda: 42, on_success=values.append)
        assert future.result(timeout=2) == 42
        assert values == [42]
    finally:
        runner.shutdown()


def test_task_runner_surfaces_worker_exception():
    runner = TaskRunner(max_workers=1)
    errors = []

    def explode():
        raise ValueError("boom")

    try:
        future = runner.submit(explode, on_error=errors.append)
        try:
            future.result(timeout=2)
        except ValueError:
            pass
        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
    finally:
        runner.shutdown()


def test_task_runner_rejects_work_after_shutdown():
    runner = TaskRunner(max_workers=1)
    runner.shutdown()
    try:
        runner.submit(lambda: None)
    except RuntimeError as exc:
        assert "closed" in str(exc)
    else:
        raise AssertionError("closed runner accepted new work")
