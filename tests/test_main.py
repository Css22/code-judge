import pytest
import json

def test_status(test_client):
    """
    Test the /status endpoint.
    """
    response = test_client.get('/status')
    assert response.status_code == 200
    assert response.json() == {
        'queue': 0,
        'num_workers': 4
    }


@pytest.mark.parametrize("type", ["judge", "run"])
def test_cpp(test_client, type):
    data = {
        "type": "cpp",
        "solution": """#include <cstdio>
#include <unistd.h>
int main(){sleep(3);printf("a");return 0;}
""",
        "expected_output": "a"
    }
    response = test_client.post(f'/{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['run_success']
    assert response.json()['success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_cpp_timeout(test_client, type):
    data = {
        "type": "cpp",
        "solution": """#include <cstdio>
#include <unistd.h>
int main(){sleep(10);printf("a");return 0;}
""",
        "expected_output": "a"
    }
    response = test_client.post(f'/{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['run_success']
    assert not response.json()['success']
    assert response.json()['reason'] == 'worker_timeout'
    if type == 'run':
        assert response.json()['stdout'].strip() == 'Suicide from timeout.'


@pytest.mark.parametrize("type", ["judge", "run"])
def test_cpp_fail(test_client, type):
    data = {
        "type": "cpp",
        "solution": """#include <cstdio>
int main(){printf("a");return 0;}
""",
        "expected_output": "b"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['run_success']
    assert not response.json()['success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_cpp_compile_error(test_client, type):
    # compile error
    data = {
        "type": "cpp",
        "solution": """#include <cstdio>
int main(){printf("a")xx;return 0;}
""",
        "expected_output": "b"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['run_success']
    assert not response.json()['success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python(test_client, type):
    data = {
        "type": "python",
        "solution": "print(input())",
        "input": "a",
        "expected_output": "a"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_timeout(test_client, type):
    data = {
        "type": "python",
        "solution": "from time import sleep\nsleep(10)",
        "input": "a",
        "expected_output": "a"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert not response.json()['run_success']
    assert response.json()['reason'] == 'worker_timeout'
    if type == 'run':
        assert response.json()['stdout'].strip() == 'Suicide from timeout.'


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_fail(test_client, type):
    data = {
        "type": "python",
        "solution": "print(input())",
        "input": "a",
        "expected_output": "b"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_missing_input(test_client, type):
    data = {
        "type": "python",
        "solution": "print(input())",
        "input": "",
        "expected_output": "a"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert not response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_batch(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "cpp",
        "solution": """#include <cstdio>
int main(){printf("a");return 0;}
""",
        "expected_output": "b"
        }, {
        "type": "python",
        "solution": "print(input())",
        "input": "a",
        "expected_output": "b"
        }, {
            "type": "python",
            "solution": "print(input())",
            "input": "a",
            "expected_output": "a"
        }, {
            "type": "cpp",
            "solution": """#include <cstdio>
#include <unistd.h>
int main(){sleep(3);printf("a");return 0;}
""",
            "expected_output": "a"
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)
    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 4
    assert not results[0]['success']
    assert results[0]['run_success']
    assert not results[1]['success']
    assert results[1]['run_success']
    assert results[2]['success']
    assert results[2]['run_success']
    assert results[3]['success']
    assert results[3]['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_batch_fail(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "python",
        "solution": "print(input())",
        "input": "",
        "expected_output": "b"
        }, {
            "type": "python",
            "solution": "print(input())",
            "input": "a",
            "expected_output": "a"
        }, {
        "type": "python",
        "solution": "print(input())",
        "input": "",
        "expected_output": "b"
        }, {
            "type": "python",
            "solution": "print(input())",
            "input": "a",
            "expected_output": "a"
        },{
        "type": "python",
        "solution": "print(input())",
        "input": "",
        "expected_output": "b"
        }, {
            "type": "python",
            "solution": "print(input())",
            "input": "a",
            "expected_output": "a"
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)
    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 6
    assert not results[0]['success']
    assert not results[0]['run_success']
    assert results[1]['success']
    assert results[1]['run_success']
    assert not results[2]['success']
    assert not results[2]['run_success']
    assert results[3]['success']
    assert results[3]['run_success']
    assert not results[4]['success']
    assert not results[4]['run_success']
    assert results[5]['success']
    assert results[5]['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_multi_process(test_client, type):
    code = """
from time import sleep
import os
from multiprocessing import Process


def worker():
    print('Worker process started')
    sleep(100)
    print('Worker process finished')


print('PP: Starting worker process')
# Start a worker process
p = Process(target=worker)
p.start()
print('worker:', os.getpid())
sleep(1)
print('PP: Worker process Finished, but leaving its child process running')
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": "a"
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert not response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_io_valid(test_client, type):
    code = """
with open('test.txt', 'w') as f:
    f.write('Hello, world!')
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": ""
    }
    response = test_client.post(f'{type}/', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_io_invalid(test_client, type):
    from pathlib import Path
    test_file = Path('/tmp/test.txt')
    test_file.unlink(missing_ok=True)
    code = """
import pathlib
print(pathlib.Path('.').resolve())
with open('../test.txt', 'w') as f:
    f.write('Hello, world!')
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": ""
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200

    print(f"Jailbreak Status (Is sandbox enabled): {not Path('/tmp/test.txt').exists()}")


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_time_control(test_client, type):
    code = """
import time
result=input()
time.sleep(20)
print(result)
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "a",
        "expected_output": "a",
        'timeout': 30
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_time_control_timeout(test_client, type):
    code = """
import time
time.sleep(60)
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": "",
        'timeout': 50
    }
    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert not response.json()['run_success']
    assert response.json()['reason'] == 'worker_timeout'
    if type == 'run':
        assert response.json()['stdout'].strip() == 'Suicide from timeout.'


@pytest.mark.parametrize("type", ["judge", "run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_python_time_control_batch(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "python",
        "solution": """
import time
result=input()
time.sleep(40)
print(result)""",
        "input": "b",
        "expected_output": "b",
        "timeout": 50
        },{
        "type": "python",
        "solution": """
import time
result=input()
time.sleep(20)
print(result)""",
        "input": "a",
        "expected_output": "a",
        "timeout": 10
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)

    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 2
    assert  results[0]['success']
    assert  results[0]['run_success']
    assert not results[1]['success']
    assert not results[1]['run_success']
    assert results[1]['reason'] == 'worker_timeout'


@pytest.mark.parametrize("type", ["judge", "run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_python_memory_limit_batch(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "python",
        "solution": """
import ctypes, time
result=input()
time.sleep(1)
buf = ctypes.create_string_buffer(600 * 1024 * 1024) # 600MB
print(result)""",
        "input": "b",
        "expected_output": "b",
        'memory_limit': 650 # 650MB
        },{
        "type": "python",
        "solution": """
import ctypes, time
result=input()
buf = ctypes.create_string_buffer(600 * 1024 * 1024) # 600MB
time.sleep(1)
print(result)""",
        "input": "a",
        "expected_output": "a",
        'memory_limit': 400 # 400MB
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)

    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 2
    assert  results[0]['success']
    assert  results[0]['run_success']
    assert not results[1]['success']
    assert not results[1]['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_cpu_core_limit(test_client, type):
    code = """
import os, multiprocessing, time, math

def burn_cpu(seconds=10):
    start = time.process_time()
    while time.process_time() - start < seconds:
        math.sqrt(123.456)   

def main():
    N_PROCS = 4
    CPU_SEC = 10          

    procs = [multiprocessing.Process(target=burn_cpu, args=(CPU_SEC,)) for _ in range(N_PROCS)]

    wall_start = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    wall_end = time.time()
    if wall_end - wall_start < 11 and wall_end - wall_start > 9:
        print("success")
    else:
        print("failed")
if __name__ == "__main__":
    main()

"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": "success",
        'timeout': 60,
        'cpu_core': 4
    }

    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["judge", "run"])
def test_python_cpu_core_limit_exceed(test_client, type):
    code = """
import os, multiprocessing, time, math

def burn_cpu(seconds=10):
    start = time.process_time()
    while time.process_time() - start < seconds:
        math.sqrt(123.456)   

def main():
    N_PROCS = 4
    CPU_SEC = 10          

    procs = [multiprocessing.Process(target=burn_cpu, args=(CPU_SEC,)) for _ in range(N_PROCS)]

    wall_start = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    wall_end = time.time()
    if wall_end - wall_start < 21 and wall_end - wall_start > 19:
        print("success")
    else:
        print("failed")
if __name__ == "__main__":
    main()
"""
    data = {
        "type": "python",
        "solution": code,
        "input": "",
        "expected_output": "success",
        'timeout': 60,
        'cpu_core': 2
    }

    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']

    
@pytest.mark.parametrize("type", ["judge", "run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_python_cpu_core_limit_batch(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "python",
        "solution": """
import os, multiprocessing, time, math

def burn_cpu(seconds=10):
    start = time.process_time()
    while time.process_time() - start < seconds:
        math.sqrt(123.456)   

def main():
    N_PROCS = 4
    CPU_SEC = 10          

    procs = [multiprocessing.Process(target=burn_cpu, args=(CPU_SEC,)) for _ in range(N_PROCS)]

    wall_start = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    wall_end = time.time()
    if wall_end - wall_start < 11 and wall_end - wall_start > 9:
        print("success")
    else:
        print("wall_end - wall_start")
if __name__ == "__main__":
    main()
""",
        "input": "",
        "expected_output": "success",
        'timeout': 60,
        'cpu_core': 4
        },{
        "type": "python",
        "solution": """
import os, multiprocessing, time, math

def burn_cpu(seconds=10):
    start = time.process_time()
    while time.process_time() - start < seconds:
        math.sqrt(123.456)   

def main():
    N_PROCS = 16
    CPU_SEC = 10          

    procs = [multiprocessing.Process(target=burn_cpu, args=(CPU_SEC,)) for _ in range(N_PROCS)]

    wall_start = time.time()
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    wall_end = time.time()
    if wall_end - wall_start < 21 and wall_end - wall_start > 19:
        print("success")
    else:
        print("wall_end - wall_start")
if __name__ == "__main__":
    main()
""",
        "input": "",
        "expected_output": "success",
        'timeout': 60,
        'cpu_core': 8
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)

    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 2
    assert results[0]['success']
    assert results[0]['run_success']
    assert results[1]['success']
    assert results[1]['run_success']


@pytest.mark.parametrize("type", ["run"])
def test_lean_error_fail(test_client, type):
    code = """
open BigOperators Real Nat Topology Rat

theorem mathd_algebra_76 (f : ℤ → ℤ)
    (h₀ : ∀ n, Odd n → f n = n ^ 2)
    (h₁ : ∀ n, Even n → f n = n ^ 2 - 4 * n - 1) :
    f 4 = -1 := by
  -- Step 1: Show that 4 is even
  have h2 : Even 4 := by
    clear * -
    bfsaesopLoop
  -- Step 2: Apply the condition for even n
  have h3 : f 4 = 4 ^ 2 - 4 * 4 - 1 := by
    clear * - h₁ h2
    bfsaesopLoop
  -- Step 3: Compute 4^2
  have h4 : (4 : ℤ) ^ 2 = 16 := by
    clear * -
    bfsaesopLoop
  -- Step 4: Compute 4 * 4
  have h5 : (4 : ℤ) * 4 = 16 := by
    clear * -
    bfsaesopLoop
  -- Step 5: Compute 16 - 16
  have h6 : (16 : ℤ) - 16 = 0 := by
    clear * -
    bfsaesopLoop
  -- Step 6: Compute 0 - 1
  have h7 : (0 : ℤ) - 1 = -1 := by
    clear * -
    bfsaesopLoop
  -- Step 7: Combine results to show f 4 = -1
  clear * - h3 h4 h5 h6 h7
  bfsaesopLoop

"""
    data = {
        "type": "lean",
        "solution": code,
        "input": "",
        "expected_output": '',
        'timeout': 2000,
        'cpu_core': 24
    }

    expect_error_info = {
        "messages": [
            {
                "severity": "error",
                "pos": {"line": 12, "column": 5},
                "endPos": None,
                "data": "unknown tactic"
            },
            {
                "severity": "error",
                "pos": {"line": 10, "column": 22},
                "endPos": {"line": 12, "column": 16},
                "data": "unsolved goals\n⊢ Even 4"
            },
            {
                "severity": "error",
                "pos": {"line": 8, "column": 16},
                "endPos": {"line": 12, "column": 16},
                "data": "unsolved goals\nf : ℤ → ℤ\nh₀ : ∀ (n : ℤ), Odd n → f n = n ^ 2\nh₁ : ∀ (n : ℤ), Even n → f n = n ^ 2 - 4 * n - 1\nh2 : Even 4\n⊢ f 4 = -1"
            }
        ],
        "env": 0
    }

    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert response.json()['run_success']
    actual_obj = json.loads(response.json()['stderr'])
    assert actual_obj == expect_error_info


@pytest.mark.parametrize("type", ["run"])
def test_lean_sorry_fail(test_client, type):
    code = """
open BigOperators Real Nat Topology Rat

theorem imo_2019_p1 (f : ℤ → ℤ) :
  (∀ a b, f (2 * a) + 2 * f b = f (f (a + b)))
    ↔ ∀ z, f z = 0 ∨ ∃ c, ∀ z, f z = 2 * z + c := by
  -- Step 1: Assume the functional equation holds
  constructor
  · intro h
    -- Step 2: Set a = 0
    have step2 : ∀ b, f 0 + 2 * f b = f (f b) := by
      clear * - h
      intro b
      have h1 := h 0 b
      simp_all
    -- Step 3: Set b = 0
    have step3 : ∀ a, f (2 * a) + 2 * f 0 = f (f a) := by
      clear * - h
      intro a
      simp_all
    -- Step 4: Combine step2 and step3
    have step4 : ∀ b, f (2 * b) = 2 * f b - f 0 := by
      clear * - step2 step3
      intro b
      linarith [step3 b, step2 b]
    -- Step 5: Assume f is linear
    let c := f 0
    -- Step 6: Consider two cases - f is constant or linear
    by_cases h_const : ∀ z, f z = c
    · -- Constant case
      have const_case : ∀ z, f z = 0 := by
        clear * - step2 h_const
        intro z
        simp_all
      intro z
      simp_all
    · -- Linear case
      push_neg at h_const
      obtain ⟨z0, hz0⟩ := h_const
      -- Step 7: Show f must be of form 2z + c
      have linear_case : ∃ c, ∀ z, f z = 2 * z + c := by
        sorry
      intro z
      obtain ⟨w, h₁⟩ := linear_case
      simp_all
  · intro h
    -- Step 8: Verify both cases satisfy the original equation
    sorry
"""
    data = {
        "type": "lean",
        "solution": code,
        "input": "",
        "expected_output": "",
        'timeout': 2000,
        'cpu_core': 24
    }

    expect_error_info = expect_error_info = {
    "sorries": [
        {
            "proofState": 0,
            "pos": {"line": 43, "column": 8},
            "goal": "f : ℤ → ℤ\nh : ∀ (a b : ℤ), f (2 * a) + 2 * f b = f (f (a + b))\nstep2 : ∀ (b : ℤ), f 0 + 2 * f b = f (f b)\nstep3 : ∀ (a : ℤ), f (2 * a) + 2 * f 0 = f (f a)\nstep4 : ∀ (b : ℤ), f (2 * b) = 2 * f b - f 0\nc : ℤ := f 0\nz0 : ℤ\nhz0 : f z0 ≠ c\n⊢ ∃ c, ∀ (z : ℤ), f z = 2 * z + c",
            "endPos": {"line": 43, "column": 13}
        },
        {
            "proofState": 1,
            "pos": {"line": 49, "column": 4},
            "goal": "case mpr\nf : ℤ → ℤ\nh : ∀ (z : ℤ), f z = 0 ∨ ∃ c, ∀ (z : ℤ), f z = 2 * z + c\n⊢ ∀ (a b : ℤ), f (2 * a) + 2 * f b = f (f (a + b))",
            "endPos": {"line": 49, "column": 9}
        }
    ],
    "messages": [
        {
            "severity": "warning",
            "pos": {"line": 5, "column": 8},
            "endPos": {"line": 5, "column": 19},
            "data": "declaration uses 'sorry'"
        }
    ],
    "env": 0
}

    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert not response.json()['success']
    assert response.json()['run_success']
    actual_obj = json.loads(response.json()['stderr'])
    assert actual_obj == expect_error_info


@pytest.mark.parametrize("type", ["run"])
def test_lean_pass(test_client, type):
    code = """
open BigOperators Real Nat Topology Rat

theorem mathd_algebra_80 (x : ℝ) (h₀ : x ≠ -1) (h₁ : (x - 9) / (x + 1) = 2) : x = -11 := by
  -- Step 1: Multiply both sides by (x + 1)
  have h2 : x - 9 = 2 * (x + 1) := by
    clear * - h₁ h₀
    rw [eq_comm]
    rw [← h₁]
    rw [div_mul_cancel₀]
    exact fun h => h₀ (by linarith)
  
  -- Step 2: Expand the right side
  have h3 : x - 9 = 2 * x + 2 := by
    clear * - h2
    (linarith)
  
  -- Step 3: Subtract x from both sides
  have h4 : -9 = x + 2 := by
    clear * - h3
    (linarith)
  
  -- Step 4: Subtract 2 from both sides
  have h5 : -11 = x := by
    clear * - h4
    (linarith)
  
  -- Step 5: Symmetry of equality
  exact h5.symm

"""
    data = {
        "type": "lean",
        "solution": code,
        "input": "",
        "expected_output": "",
        'timeout': 2000,
        'cpu_core': 24
    }


    response = test_client.post(f'{type}', json=data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['success']
    assert response.json()['run_success']


@pytest.mark.parametrize("type", ["run"])
@pytest.mark.parametrize("batch_type", ["batch", "long-batch"])
def test_lean_batch(test_client, type, batch_type):
    data = {
        'type': 'batch',
        "submissions": [{
        "type": "lean",
        "solution": """
open BigOperators Real Nat Topology Rat

theorem mathd_algebra_80 (x : ℝ) (h₀ : x ≠ -1) (h₁ : (x - 9) / (x + 1) = 2) : x = -11 := by
  -- Step 1: Multiply both sides by (x + 1)
  have h2 : x - 9 = 2 * (x + 1) := by
    clear * - h₁ h₀
    rw [eq_comm]
    rw [← h₁]
    rw [div_mul_cancel₀]
    exact fun h => h₀ (by linarith)
  
  -- Step 2: Expand the right side
  have h3 : x - 9 = 2 * x + 2 := by
    clear * - h2
    (linarith)
  
  -- Step 3: Subtract x from both sides
  have h4 : -9 = x + 2 := by
    clear * - h3
    (linarith)
  
  -- Step 4: Subtract 2 from both sides
  have h5 : -11 = x := by
    clear * - h4
    (linarith)
  
  -- Step 5: Symmetry of equality
  exact h5.symm
  """,
        "input": "",
        "expected_output": "",
        'memory_limit': 650,
        'timeout': 2000,
        'cpu_core': 24
        },{
        "type": "lean",
        "solution": """
open BigOperators Real Nat Topology Rat

theorem imo_2019_p1 (f : ℤ → ℤ) :
  (∀ a b, f (2 * a) + 2 * f b = f (f (a + b)))
    ↔ ∀ z, f z = 0 ∨ ∃ c, ∀ z, f z = 2 * z + c := by
  -- Step 1: Assume the functional equation holds
  constructor
  · intro h
    -- Step 2: Set a = 0
    have step2 : ∀ b, f 0 + 2 * f b = f (f b) := by
      clear * - h
      intro b
      have h1 := h 0 b
      simp_all
    -- Step 3: Set b = 0
    have step3 : ∀ a, f (2 * a) + 2 * f 0 = f (f a) := by
      clear * - h
      intro a
      simp_all
    -- Step 4: Combine step2 and step3
    have step4 : ∀ b, f (2 * b) = 2 * f b - f 0 := by
      clear * - step2 step3
      intro b
      linarith [step3 b, step2 b]
    -- Step 5: Assume f is linear
    let c := f 0
    -- Step 6: Consider two cases - f is constant or linear
    by_cases h_const : ∀ z, f z = c
    · -- Constant case
      have const_case : ∀ z, f z = 0 := by
        clear * - step2 h_const
        intro z
        simp_all
      intro z
      simp_all
    · -- Linear case
      push_neg at h_const
      obtain ⟨z0, hz0⟩ := h_const
      -- Step 7: Show f must be of form 2z + c
      have linear_case : ∃ c, ∀ z, f z = 2 * z + c := by
        sorry
      intro z
      obtain ⟨w, h₁⟩ := linear_case
      simp_all
  · intro h
    -- Step 8: Verify both cases satisfy the original equation
    sorry
    """,
        "input": "",
        "expected_output": "",
        'memory_limit': 400,
        'timeout': 2000,
        'cpu_core': 24
        }]
    }
    response = test_client.post(f'{type}/{batch_type}', json=data)

    print(response.json())
    assert response.status_code == 200
    results = response.json()['results']

    assert len(results) == 2
    assert  results[0]['success']
    assert  results[0]['run_success']
    assert not results[1]['success']
    assert results[1]['run_success']