
-- Tested it can go anywhere on HKS
function UpdateAttack()
    if AttackCommonFunction("W_AttackRightLight1", "W_AttackRightHeavy1Start", "W_AttackLeftLight1",
        "W_AttackLeftHeavy1", "W_AttackBothLight1", "W_AttackBothHeavy1Start", FALSE, TRUE, 0) == TRUE then
        return
    end
end

-- Example of functions. This is so that you can cancel animations
function Attack1_onUpdate()
    UpdateAttack()
end

function Attack2_onUpdate()
    UpdateAttack()
end

function Attack3_onUpdate()
    UpdateAttack()
end

-- Or you can use this one. Only choose one of them

-- Update
function UpdateAnime()
    if AttackCommonFunction("W_AttackRightLight1", "W_AttackRightHeavy1Start", "W_AttackLeftLight1",
        "W_AttackLeftHeavy1", "W_AttackBothLight1", "W_AttackBothHeavy1Start", FALSE, TRUE, 0) == TRUE then
        return
    end
end

-- Custom Anime Handler
function AnimeNameHere_onUpdate() UpdateAnime() end
function AnimeNameHere_onUpdate() UpdateAnime() end
function AnimeNameHere_onUpdate() UpdateAnime() end
