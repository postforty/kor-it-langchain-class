"""
순수 Python으로 GPT를 학습하고 추론하는 가장 원자적인 방법.
이 파일이 완전한 알고리즘입니다.
나머지는 모두 효율성을 위한 것입니다.
@karpathy
https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95
"""

import os       # 파일 존재 확인용
import math     # 로그, 지수 계산용
import random   # 난수 생성, 샘플링용
random.seed(42) # 재현 가능한 난수를 위한 시드 설정

# 데이터셋 준비: 문서(예: 이름) 리스트를 `docs`에 저장
if not os.path.exists('input.txt'):
    import urllib.request
    names_url = 'https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt'
    urllib.request.urlretrieve(names_url, 'input.txt')  # 데이터가 없으면 다운로드
docs = [line.strip() for line in open('input.txt') if line.strip()]  # 각 줄을 읽어서 리스트로 저장
random.shuffle(docs)  # 데이터를 무작위로 섞음
print(f"num docs: {len(docs)}")

# 토크나이저: 문자열을 정수 시퀀스("토큰")로 변환하고 그 반대도 수행
uchars = sorted(set(''.join(docs)))  # 데이터셋의 고유 문자들을 토큰 ID 0..n-1로 사용
BOS = len(uchars)  # 특수 토큰: 시퀀스 시작(Beginning of Sequence)을 나타내는 토큰 ID
vocab_size = len(uchars) + 1  # 전체 고유 토큰 수 (고유 문자 + BOS 토큰)
print(f"vocab size: {vocab_size}")

# 자동 미분(Autograd): 계산 그래프를 통해 연쇄 법칙을 재귀적으로 적용
class Value:
    __slots__ = ('data', 'grad', '_children', '_local_grads')  # 메모리 사용 최적화

    def __init__(self, data, children=(), local_grads=()):
        self.data = data                # 순전파 시 계산된 이 노드의 스칼라 값
        self.grad = 0                   # 역전파 시 계산된 손실에 대한 이 노드의 미분값(그래디언트)
        self._children = children       # 계산 그래프에서 이 노드의 자식 노드들
        self._local_grads = local_grads # 자식 노드에 대한 이 노드의 지역 미분값

    def __add__(self, other):
        # 덧셈 연산: 두 값을 더하고 그래디언트 계산을 위한 정보 저장
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, (self, other), (1, 1))

    def __mul__(self, other):
        # 곱셈 연산: 두 값을 곱하고 그래디언트 계산을 위한 정보 저장
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, (self, other), (other.data, self.data))

    def __pow__(self, other): return Value(self.data**other, (self,), (other * self.data**(other-1),))  # 거듭제곱
    def log(self): return Value(math.log(self.data), (self,), (1/self.data,))  # 자연로그
    def exp(self): return Value(math.exp(self.data), (self,), (math.exp(self.data),))  # 지수함수
    def relu(self): return Value(max(0, self.data), (self,), (float(self.data > 0),))  # ReLU 활성화
    def __neg__(self): return self * -1  # 부호 반전
    def __radd__(self, other): return self + other  # 역 덧셈
    def __sub__(self, other): return self + (-other)  # 뺄셈
    def __rsub__(self, other): return other + (-self)  # 역 뺄셈
    def __rmul__(self, other): return self * other  # 역 곱셈
    def __truediv__(self, other): return self * other**-1  # 나눗셈
    def __rtruediv__(self, other): return other * self**-1  # 역 나눗셈

    def backward(self):
        # 역전파: 위상 정렬된 순서로 그래디언트를 계산
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._children:
                    build_topo(child)
                topo.append(v)
        build_topo(self)  # 계산 그래프를 위상 정렬
        self.grad = 1  # 손실 자체의 그래디언트는 1
        for v in reversed(topo):  # 역순으로 순회하며 그래디언트 전파
            for child, local_grad in zip(v._children, v._local_grads):
                child.grad += local_grad * v.grad  # 연쇄 법칙 적용

# 모델 파라미터 초기화: 모델의 지식을 저장할 가중치들
n_layer = 1     # 트랜스포머 신경망의 깊이 (레이어 수)
n_embd = 16     # 네트워크의 너비 (임베딩 차원)
block_size = 16 # 어텐션 윈도우의 최대 컨텍스트 길이 (참고: 가장 긴 이름이 15자)
n_head = 4      # 어텐션 헤드 수
head_dim = n_embd // n_head  # 각 헤드의 차원 (파생값)
matrix = lambda nout, nin, std=0.08: [[Value(random.gauss(0, std)) for _ in range(nin)] for _ in range(nout)]  # 가중치 행렬 생성 함수
state_dict = {'wte': matrix(vocab_size, n_embd), 'wpe': matrix(block_size, n_embd), 'lm_head': matrix(vocab_size, n_embd)}  # 토큰 임베딩, 위치 임베딩, 출력 레이어
for i in range(n_layer):
    # 각 레이어의 어텐션 가중치 (Query, Key, Value, Output)
    state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)
    # 각 레이어의 MLP(Feed-Forward) 가중치
    state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)
    state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)
params = [p for mat in state_dict.values() for row in mat for p in row]  # 모든 파라미터를 1차원 리스트로 평탄화
print(f"num params: {len(params)}")

# 모델 아키텍처 정의: 토큰과 파라미터를 다음 토큰의 로짓으로 매핑하는 함수
# GPT-2를 따르되 약간의 차이: layernorm -> rmsnorm, 바이어스 없음, GeLU -> ReLU
def linear(x, w):
    # 선형 변환: 행렬 곱셈 수행
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]

def softmax(logits):
    # 소프트맥스: 로짓을 확률 분포로 변환 (수치 안정성을 위해 최댓값 빼기)
    max_val = max(val.data for val in logits)
    exps = [(val - max_val).exp() for val in logits]
    total = sum(exps)
    return [e / total for e in exps]

def rmsnorm(x):
    # RMS 정규화: 평균 제곱근으로 정규화 (LayerNorm의 간소화 버전)
    ms = sum(xi * xi for xi in x) / len(x)
    scale = (ms + 1e-5) ** -0.5
    return [xi * scale for xi in x]

def gpt(token_id, pos_id, keys, values):
    # GPT 모델의 순전파: 토큰과 위치를 입력받아 다음 토큰의 로짓을 출력
    tok_emb = state_dict['wte'][token_id]  # 토큰 임베딩
    pos_emb = state_dict['wpe'][pos_id]    # 위치 임베딩
    x = [t + p for t, p in zip(tok_emb, pos_emb)]  # 토큰과 위치 임베딩을 합침
    x = rmsnorm(x)  # 정규화 (잔차 연결로 인한 역전파를 위해 필요)

    for li in range(n_layer):
        # 1) 멀티헤드 어텐션 블록
        x_residual = x  # 잔차 연결을 위해 입력 저장
        x = rmsnorm(x)
        q = linear(x, state_dict[f'layer{li}.attn_wq'])  # Query 계산
        k = linear(x, state_dict[f'layer{li}.attn_wk'])  # Key 계산
        v = linear(x, state_dict[f'layer{li}.attn_wv'])  # Value 계산
        keys[li].append(k)    # 현재 Key를 캐시에 추가 (이전 토큰들과 어텐션하기 위해)
        values[li].append(v)  # 현재 Value를 캐시에 추가
        x_attn = []
        for h in range(n_head):  # 각 어텐션 헤드별로 처리
            hs = h * head_dim
            q_h = q[hs:hs+head_dim]  # 현재 헤드의 Query
            k_h = [ki[hs:hs+head_dim] for ki in keys[li]]    # 모든 위치의 Key
            v_h = [vi[hs:hs+head_dim] for vi in values[li]]  # 모든 위치의 Value
            # 어텐션 스코어 계산: Query와 모든 Key의 내적 (스케일링 적용)
            attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5 for t in range(len(k_h))]
            attn_weights = softmax(attn_logits)  # 어텐션 가중치로 변환
            # 가중치를 적용한 Value의 가중합 계산
            head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h))) for j in range(head_dim)]
            x_attn.extend(head_out)  # 헤드 출력을 연결
        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])  # 출력 프로젝션
        x = [a + b for a, b in zip(x, x_residual)]  # 잔차 연결
        
        # 2) MLP(Feed-Forward) 블록
        x_residual = x  # 잔차 연결을 위해 입력 저장
        x = rmsnorm(x)
        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])  # 첫 번째 선형 변환 (확장)
        x = [xi.relu() for xi in x]  # ReLU 활성화 함수
        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])  # 두 번째 선형 변환 (축소)
        x = [a + b for a, b in zip(x, x_residual)]  # 잔차 연결

    logits = linear(x, state_dict['lm_head'])  # 최종 출력: 어휘 크기만큼의 로짓
    return logits

# Adam 옵티마이저와 버퍼 초기화
learning_rate, beta1, beta2, eps_adam = 0.01, 0.85, 0.99, 1e-8
m = [0.0] * len(params)  # 1차 모멘트 버퍼 (그래디언트의 지수 이동 평균)
v = [0.0] * len(params)  # 2차 모멘트 버퍼 (그래디언트 제곱의 지수 이동 평균)

# 학습 루프 시작
num_steps = 1000  # 학습 스텝 수
for step in range(num_steps):

    # 단일 문서를 가져와서 토큰화하고, 양쪽에 BOS 특수 토큰 추가
    doc = docs[step % len(docs)]
    tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
    n = min(block_size, len(tokens) - 1)

    # 순전파: 토큰 시퀀스를 모델에 통과시켜 손실까지 계산 그래프 구축
    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]  # KV 캐시 초기화
    losses = []
    for pos_id in range(n):
        token_id, target_id = tokens[pos_id], tokens[pos_id + 1]  # 현재 토큰과 다음 토큰(정답)
        logits = gpt(token_id, pos_id, keys, values)  # 모델 순전파
        probs = softmax(logits)  # 확률 분포로 변환
        loss_t = -probs[target_id].log()  # 크로스 엔트로피 손실 (음의 로그 우도)
        losses.append(loss_t)
    loss = (1 / n) * sum(losses)  # 문서 시퀀스에 대한 평균 손실

    # 역전파: 모든 모델 파라미터에 대한 그래디언트 계산
    loss.backward()

    # Adam 옵티마이저 업데이트: 그래디언트를 기반으로 모델 파라미터 갱신
    lr_t = learning_rate * (1 - step / num_steps)  # 선형 학습률 감쇠
    for i, p in enumerate(params):
        m[i] = beta1 * m[i] + (1 - beta1) * p.grad  # 1차 모멘트 업데이트
        v[i] = beta2 * v[i] + (1 - beta2) * p.grad ** 2  # 2차 모멘트 업데이트
        m_hat = m[i] / (1 - beta1 ** (step + 1))  # 바이어스 보정된 1차 모멘트
        v_hat = v[i] / (1 - beta2 ** (step + 1))  # 바이어스 보정된 2차 모멘트
        p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)  # 파라미터 업데이트
        p.grad = 0  # 그래디언트 초기화

    print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}", end='\r')

# 추론: 학습된 모델로 새로운 텍스트 생성
temperature = 0.5  # (0, 1] 범위, 생성 텍스트의 "창의성" 조절 (낮을수록 보수적, 높을수록 다양함)
print("\n--- inference (new, hallucinated names) ---")
for sample_idx in range(20):
    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]  # KV 캐시 초기화
    token_id = BOS  # 시작 토큰
    sample = []
    for pos_id in range(block_size):
        logits = gpt(token_id, pos_id, keys, values)  # 다음 토큰 예측
        probs = softmax([l / temperature for l in logits])  # temperature로 확률 분포 조정
        token_id = random.choices(range(vocab_size), weights=[p.data for p in probs])[0]  # 확률에 따라 샘플링
        if token_id == BOS:  # BOS 토큰이 나오면 생성 종료
            break
        sample.append(uchars[token_id])  # 생성된 문자 추가
    print(f"sample {sample_idx+1:2d}: {''.join(sample)}")