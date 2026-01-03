# Commission Split Logic

## Understanding the MLM Commission Structure

### Hierarchy Example 1: John → Emily → Luke

**When Luke closes a deal (has a client):**

| CTV | Level | Relationship | Commission Rate | Who Gets It |
|-----|-------|--------------|----------------|-------------|
| Luke | L0 | The one who closed the deal | 25% | Luke |
| Emily | L1 | Luke's direct referrer (1 level up) | 5% | Emily |
| John | L2 | Emily's referrer (2 levels up) | 2.5% | John |

**Example Calculation:**
- Service Total (tong_tien): 1,000,000 VND
- Luke's commission (L0): 1,000,000 × 25% = 250,000 VND
- Emily's commission (L1): 1,000,000 × 5% = 50,000 VND
- John's commission (L2): 1,000,000 × 2.5% = 25,000 VND
- **Total Commission Paid**: 325,000 VND

---

### Hierarchy Example 2: Alice → Bob → Carol → David

**When David closes a deal:**

| CTV | Level | Relationship | Commission Rate | Who Gets It |
|-----|-------|--------------|----------------|-------------|
| David | L0 | The one who closed the deal | 25% | David |
| Carol | L1 | David's direct referrer (1 level up) | 5% | Carol |
| Bob | L2 | Carol's referrer (2 levels up) | 2.5% | Bob |
| Alice | L3 | Bob's referrer (3 levels up) | 1.25% | Alice |

**Example Calculation:**
- Service Total (tong_tien): 2,000,000 VND
- David's commission (L0): 2,000,000 × 25% = 500,000 VND
- Carol's commission (L1): 2,000,000 × 5% = 100,000 VND
- Bob's commission (L2): 2,000,000 × 2.5% = 50,000 VND
- Alice's commission (L3): 2,000,000 × 1.25% = 25,000 VND
- **Total Commission Paid**: 675,000 VND

---

### Hierarchy Example 3: Root → A → B → C → D

**When D closes a deal (5 levels deep):**

| CTV | Level | Relationship | Commission Rate | Who Gets It |
|-----|-------|--------------|----------------|-------------|
| D | L0 | The one who closed the deal | 25% | D |
| C | L1 | D's direct referrer (1 level up) | 5% | C |
| B | L2 | C's referrer (2 levels up) | 2.5% | B |
| A | L3 | B's referrer (3 levels up) | 1.25% | A |
| Root | L4 | A's referrer (4 levels up) | 0.625% | Root |

**Example Calculation:**
- Service Total (tong_tien): 5,000,000 VND
- D's commission (L0): 5,000,000 × 25% = 1,250,000 VND
- C's commission (L1): 5,000,000 × 5% = 250,000 VND
- B's commission (L2): 5,000,000 × 2.5% = 125,000 VND
- A's commission (L3): 5,000,000 × 1.25% = 62,500 VND
- Root's commission (L4): 5,000,000 × 0.625% = 31,250 VND
- **Total Commission Paid**: 1,718,750 VND

---

## Key Points

1. **Commission flows UP the hierarchy** from the person who closed the deal
2. **Level 0 (L0)** = The CTV who actually closed the deal (gets 25%)
3. **Level 1 (L1)** = Direct referrer of the closer (gets 5%)
4. **Level 2 (L2)** = Referrer of L1 (gets 2.5%)
5. **Level 3 (L3)** = Referrer of L2 (gets 1.25%)
6. **Level 4 (L4)** = Referrer of L3 (gets 0.625%)
7. **Maximum depth**: 4 levels (L0 to L4)
8. **Base amount**: Always `tong_tien` (total cost) from `khach_hang` or `services` table

## Database Linking

- **khach_hang.nguoi_chot** → Links to `ctv.ma_ctv` (who closed the deal)
- **services.nguoi_chot** or **services.ctv_code** → Links to `ctv.ma_ctv` (who closed the deal)
- **ctv.nguoi_gioi_thieu** → Links to parent CTV (referrer) in hierarchy

## Commission Rates

| Level | Rate | Percentage |
|-------|------|------------|
| L0 | 0.25 | 25% |
| L1 | 0.05 | 5% |
| L2 | 0.025 | 2.5% |
| L3 | 0.0125 | 1.25% |
| L4 | 0.00625 | 0.625% |

