const rateSlabs = [
    { rate: 9.25, start: new Date('1980-01-01'), end: new Date('1996-03-31') },
    { rate: 40,   start: new Date('1996-04-01'), end: new Date('2011-03-31') },
    { rate: 80,   start: new Date('2011-04-01'), end: new Date('2016-06-30') },
    { rate: 100,  start: new Date('2016-07-01'), end: new Date('2025-03-31') },
    { rate: 150,  start: new Date('2025-04-01'), end: new Date('2050-12-31') } 
];

function formatDate(date) {
    const d = String(date.getDate()).padStart(2, '0');
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const y = date.getFullYear();
    return `${d}/${m}/${y}`;
}

function getOverlapMonths(slabStart, slabEnd, userStart, userEnd) {
    const overlapStart = new Date(Math.max(slabStart, userStart));
    const overlapEnd = new Date(Math.min(slabEnd, userEnd));

    if (overlapStart > overlapEnd) return 0; 

    let months = (overlapEnd.getFullYear() - overlapStart.getFullYear()) * 12;
    months -= overlapStart.getMonth();
    months += overlapEnd.getMonth();
    
    return months + 1; 
}

function calculateAmountForDateRange(reqStart, reqEnd) {
    if (reqStart > reqEnd) return 0;
    let amt = 0;
    rateSlabs.forEach(slab => {
        const m = getOverlapMonths(slab.start, slab.end, reqStart, reqEnd);
        if (m > 0) amt += m * slab.rate;
    });
    return amt;
}

function calculateBill() {
    const userStartInput = document.getElementById('startDate').value;
    const userEndInput = document.getElementById('endDate').value;
    const advancePayment = parseFloat(document.getElementById('advancePayment').value) || 0;
    const isLokAdalat = document.getElementById('lokAdalat').checked;

    if (!userStartInput || !userEndInput) return;

    if (advancePayment > 0 && advancePayment % 150 !== 0) {
        alert("कृपया ध्यान दें: अग्रिम भुगतान (Advance Payment) केवल 150 के गुणांक (जैसे 150, 300, 450, 600...) में ही दर्ज करें।");
        return; 
    }

    const userStart = new Date(userStartInput);
    const userEnd = new Date(userEndInput);
    
    if (userStart > userEnd) {
        alert("प्रारंभ तिथि समाप्ति तिथि से पहले की होनी चाहिए!");
        return;
    }

    const tbody = document.getElementById('slabsBody');
    tbody.innerHTML = ''; 

    let totalBill = 0;
    let lastMonthRate = 0;

    rateSlabs.forEach(slab => {
        const months = getOverlapMonths(slab.start, slab.end, userStart, userEnd);
        let amount = 0;

        if (months > 0) {
            amount = months * slab.rate;
            totalBill += amount;
        }
        
        if (userEnd >= slab.start && userEnd <= slab.end) {
            lastMonthRate = slab.rate;
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>₹${slab.rate}</td>
            <td>${formatDate(slab.start)}</td>
            <td>${formatDate(slab.end)}</td>
            <td>${months > 0 ? months : 0}</td>
            <td>₹${amount}</td>
        `;
        tbody.appendChild(tr);
    });

    const today = new Date();
    today.setHours(0, 0, 0, 0); 

    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth(); 
    
    const currentFyStartYear = currentMonth >= 3 ? currentYear : currentYear - 1;
    const currentFyStart = new Date(currentFyStartYear, 3, 1); 
    const endOfArrears = new Date(currentFyStartYear, 2, 31); 

    let arrearsBill = calculateAmountForDateRange(userStart, new Date(Math.min(userEnd, endOfArrears)));
    let currentFyBill = calculateAmountForDateRange(new Date(Math.max(userStart, currentFyStart)), userEnd);

    let penaltyableArrears = arrearsBill;
    let penaltyableCurrentFy = currentFyBill;
    
    const graceDueDate = new Date(userEnd.getFullYear(), userEnd.getMonth() + 1, 15);
    graceDueDate.setHours(0, 0, 0, 0);
    
    const isGracePeriod = today <= graceDueDate;

    if (isGracePeriod) {
        if (currentFyBill >= lastMonthRate && totalBill > 0) {
            penaltyableCurrentFy -= lastMonthRate;
        } else if (arrearsBill >= lastMonthRate && totalBill > 0) {
            penaltyableArrears -= lastMonthRate;
        }
    }

    let standardArrearsPenalty = penaltyableArrears * 0.10;
    let currentFyPenalty = penaltyableCurrentFy * 0.10; 
    let finalArrearsPenalty = standardArrearsPenalty;
    
    let discountAmt = 0; 

    const penaltyLabel = document.getElementById('penaltyLabel');
    const penaltyAmountCell = document.getElementById('penaltyAmount');
    const discountRow = document.getElementById('discountRow'); 
    const discountAmountCell = document.getElementById('discountAmount');
    
    let baseLabelText = "पेनल्टी 10%";
    if (isGracePeriod) {
        baseLabelText += ` (Grace till ${formatDate(graceDueDate)})`; 
    } else {
        baseLabelText += " (After Due)";
    }

    if (isLokAdalat) {
        if (totalBill <= 10000) {
            finalArrearsPenalty = 0; 
            discountAmt = standardArrearsPenalty; 
            penaltyLabel.innerText = baseLabelText + " - 100% Waived";
        } 
        else if (totalBill > 10000 && totalBill <= 50000) {
            finalArrearsPenalty = standardArrearsPenalty * 0.25; 
            discountAmt = standardArrearsPenalty * 0.75; 
            penaltyLabel.innerText = baseLabelText + " - 75% Waived";
        } 
        else if (totalBill > 50000) {
            finalArrearsPenalty = standardArrearsPenalty * 0.50; 
            discountAmt = standardArrearsPenalty * 0.50; 
            penaltyLabel.innerText = baseLabelText + " - 50% Waived";
        }
    } else {
        finalArrearsPenalty = standardArrearsPenalty;
        discountAmt = 0; 
        penaltyLabel.innerText = baseLabelText;
    }

    if (discountAmt > 0) {
        discountRow.style.display = 'flex'; 
        discountAmountCell.innerText = "- ₹" + discountAmt.toFixed(2);
    } else {
        discountRow.style.display = 'none'; 
    }

    const finalPenalty = finalArrearsPenalty + currentFyPenalty;
    const totalCharge = totalBill + finalPenalty + advancePayment; 

    document.getElementById('totalBillAmount').innerText = "₹" + totalBill.toFixed(2);
    document.getElementById('penaltyAmount').innerText = "₹" + finalPenalty.toFixed(2);
    document.getElementById('advPaymentDisplay').innerText = "₹" + advancePayment.toFixed(2);
    document.getElementById('finalCharge').innerText = "₹" + totalCharge.toFixed(2);

    const remarkBox = document.getElementById('remarkBox');
    if (totalCharge > 0 || totalBill > 0) {
        remarkBox.style.display = 'block';
        
        let remarkHtml = `<strong>📌 रिमार्क:</strong> दिनांक <strong>${formatDate(userStart)}</strong> से <strong>${formatDate(userEnd)}</strong> तक की कुल देय राशि <span style="font-size: 18px; font-weight: bold; color: #b91c1c;">₹${totalCharge.toFixed(2)}</span> है।`;
        
        if (discountAmt > 0) {
            remarkHtml += `<br><br><span style="color: #047857;">🎉 <em>(लोक अदालत के अंतर्गत <strong>₹${discountAmt.toFixed(2)}</strong> की पेनल्टी छूट दी गई है।)</em></span>`;
        }
        
        remarkBox.innerHTML = remarkHtml;
    } else {
        remarkBox.style.display = 'none';
    }
}

window.onload = function() {
    const today = new Date();
    const lastDayOfPrevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    
    const yyyy = lastDayOfPrevMonth.getFullYear();
    const mm = String(lastDayOfPrevMonth.getMonth() + 1).padStart(2, '0');
    const dd = String(lastDayOfPrevMonth.getDate()).padStart(2, '0');
    
    document.getElementById('endDate').value = `${yyyy}-${mm}-${dd}`;
    calculateBill();
};
