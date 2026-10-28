"""Small, source-grounded DPDP Act assistant for the offline hackathon prototype.

This is deliberately a curated FAQ, not a generative legal engine. Unknown questions
are declined instead of answered from guesswork.
"""
from __future__ import annotations

import re
from fastapi import HTTPException

SOURCES = [
    {"label": "Digital Personal Data Protection Act, 2023 (India Code)",
     "url": "https://www.indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf",
     "detail": "Act No. 22 of 2023"},
    {"label": "DPDP Rules, 2025 (MeitY Gazette)",
     "url": "https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf",
     "detail": "G.S.R. 846(E), 13 November 2025"},
    {"label": "DPDP Act commencement notification (MeitY Gazette)",
     "url": "https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf",
     "detail": "G.S.R. 843(E), 13 November 2025"},
]

FAQ = [
    {
      "id": "overview", "keys": ["what is dpdp", "dpdp act", "explain dpdp", "dpdp kya", "dpdp act kya", "digital personal data protection", "overview", "कya hai", "क्या है", "समझाओ"],
      "en": "The Digital Personal Data Protection Act, 2023 is India's law for processing digital personal data. It recognises an individual's interest in protecting personal data while allowing processing for lawful purposes. The Act defines roles, duties, rights and the framework for enforcement. The DPDP Rules, 2025 provide implementation detail.",
      "hi": "Digital Personal Data Protection Act, 2023 भारत का ऐसा कानून है जो digital personal data के processing को नियंत्रित करता है। यह व्यक्ति के personal data की सुरक्षा और वैध उद्देश्यों के लिए data processing—दोनों को मान्यता देता है। इसमें अलग-अलग पक्षों की जिम्मेदारियाँ, व्यक्ति के अधिकार और enforcement framework शामिल हैं। DPDP Rules, 2025 इसके implementation की जानकारी देते हैं。",
      "refs": ["act", "rules"]
    },
    {
      "id": "roles", "keys": ["data fiduciary", "data principal", "processor", "fiduciary", "डेटा फिड्यूशियरी", "डेटा प्रिंसिपल", "data controller"],
      "en": "A Data Principal is the individual to whom the personal data relates. A Data Fiduciary is the person who determines the purpose and means of processing personal data. A Data Processor processes personal data on behalf of a Data Fiduciary. See section 2 of the Act for statutory definitions.",
      "hi": "Data Principal वह व्यक्ति है जिससे personal data संबंधित है। Data Fiduciary वह व्यक्ति/संस्था है जो तय करती है कि personal data किस उद्देश्य से और किस तरीके से process होगा। Data Processor, Data Fiduciary की ओर से personal data process करता है। कानूनी परिभाषाओं के लिए Act की धारा 2 देखें。",
      "refs": ["act"]
    },
    {
      "id": "rights", "keys": ["rights", "right of data principal", "access", "correction", "erasure", "grievance", "nominate", "अधिकार", "सुधार", "मिटाने", "शिकायत", "नामांकित"],
      "en": "The Act provides Data Principals with rights that include access to information about personal data, correction and erasure, grievance redressal, and nomination, subject to the Act's conditions and applicable commencement. The exact procedure and exceptions must be read with the Rules and relevant provisions.",
      "hi": "Act में Data Principal को कुछ अधिकार दिए गए हैं—जैसे personal data के बारे में जानकारी प्राप्त करना, correction और erasure का अनुरोध, grievance redressal और nominee नामित करना। ये अधिकार Act की शर्तों, अपवादों और लागू commencement के अधीन हैं। सही प्रक्रिया के लिए संबंधित धाराओं के साथ Rules भी पढ़ें。",
      "refs": ["act", "rules", "commencement"]
    },
    {
      "id": "erasure", "keys": ["delete my data", "erase", "erasure", "deletion", "remove personal data", "data deletion", "मेरा डेटा", "डिलीट", "मिटाना", "हटाना", "data erase"],
      "en": "The Act recognises a Data Principal's right to seek erasure of personal data, subject to the Act and Rules. A Data Fiduciary must also retain personal data where retention is necessary for compliance with law. Therefore, erasure is not an unconditional promise that every record disappears immediately; applicable legal retention and other statutory conditions matter. See section 12 and related provisions.",
      "hi": "Act में Data Principal को personal data मिटाने (erasure) का अनुरोध करने का अधिकार दिया गया है, लेकिन यह Act और Rules की शर्तों के अधीन है। जहाँ किसी कानून का पालन करने के लिए data रखना जरूरी हो, वहाँ Data Fiduciary उसे retain कर सकता है। इसलिए हर record तुरंत और बिना अपवाद delete हो जाएगा—ऐसी गारंटी नहीं है। धारा 12 और संबंधित प्रावधान देखें。",
      "refs": ["act", "rules"]
    },
    {
      "id": "consent", "keys": ["consent", "withdraw consent", "notice", "सहमति", "consent वापस", "मंजूरी"],
      "en": "Where consent is the basis for processing, the Act requires consent to be free, specific, informed, unconditional and unambiguous, with a clear affirmative action. A Data Principal may withdraw consent, and withdrawing it should be as easy as giving it. Processing may still be permitted on another lawful basis recognised by the Act. See sections 5–6 and section 7.",
      "hi": "जहाँ processing का आधार consent है, वहाँ consent स्वतंत्र, specific, informed, unconditional और unambiguous होना चाहिए तथा स्पष्ट affirmative action से दिया जाना चाहिए। Data Principal consent वापस ले सकता है और उसे वापस लेना consent देने जितना आसान होना चाहिए। फिर भी Act में मान्य किसी अन्य lawful use के आधार पर processing संभव हो सकती है। धारा 5–7 देखें。",
      "refs": ["act", "rules"]
    },
    {
      "id": "children", "keys": ["child", "children", "minor", "parental consent", "बच्चे", "नाबालिग", "माता पिता"],
      "en": "The Act has additional requirements for processing children's personal data, including verifiable parental or guardian consent, subject to prescribed exemptions and conditions. Do not assume every service or age scenario is treated identically; consult section 9 and the applicable Rules.",
      "hi": "बच्चों के personal data को process करने के लिए Act में अतिरिक्त शर्तें हैं, जिनमें सत्यापित parental या guardian consent शामिल है। कुछ निर्धारित exemptions और शर्तें भी हो सकती हैं। हर service या उम्र की स्थिति को एक जैसा न मानें; धारा 9 और लागू Rules देखें。",
      "refs": ["act", "rules"]
    },
    {
      "id": "breach", "keys": ["data breach", "personal data breach", "breach notification", "leak", "डेटा लीक", "डेटा ब्रीच", "उल्लंघन"],
      "en": "The Act requires a Data Fiduciary to take reasonable security safeguards to prevent personal data breaches and to notify the Board and affected Data Principals of a personal data breach in the prescribed manner. The Rules provide operational detail. The precise requirements depend on the applicable provisions and commencement dates.",
      "hi": "Act के अनुसार Data Fiduciary को personal data breach रोकने के लिए उचित security safeguards अपनाने होते हैं। Personal data breach होने पर निर्धारित तरीके से Board और प्रभावित Data Principals को सूचना देने की जिम्मेदारी भी है। Rules इसकी प्रक्रिया का विवरण देते हैं। लागू requirements commencement dates पर भी निर्भर करती हैं。",
      "refs": ["act", "rules", "commencement"]
    },
    {
      "id": "grievance", "keys": ["complaint", "grievance", "board", "appeal", "शिकायत", "अपील", "बोर्ड"],
      "en": "The Act provides a grievance-redressal framework and establishes the Data Protection Board of India. A Data Principal is expected to use the Data Fiduciary's grievance-redressal mechanism before approaching the Board, as provided by the Act. The Board's powers and appeal route are set out in the Act.",
      "hi": "Act में grievance redressal की व्यवस्था है और Data Protection Board of India की स्थापना का प्रावधान है। Act के अनुसार Board के पास जाने से पहले Data Principal को Data Fiduciary की grievance mechanism का उपयोग करना होता है। Board की powers और appeal की प्रक्रिया Act में दी गई है。",
      "refs": ["act", "rules"]
    },
    {
      "id": "commencement", "keys": ["commencement", "effective date", "in force", "implementation date", "kab lagu", "लागू कब", "कब लागू", "effective", "timeline"],
      "en": "Important: the Act does not commence all at once. G.S.R. 843(E), dated 13 November 2025, appoints different commencement dates for different groups of provisions: some commenced on publication; a second group is scheduled one year after publication; and the main group is scheduled eighteen months after publication (13 May 2027, calculated from the Gazette date). Check the notification for the exact section list. Do not assume every substantive duty is already in force today.",
      "hi": "महत्वपूर्ण: Act की सभी धाराएँ एक ही तारीख से लागू नहीं हुईं। 13 नवंबर 2025 की अधिसूचना G.S.R. 843(E) अलग-अलग प्रावधानों के लिए अलग commencement dates तय करती है: कुछ प्रावधान प्रकाशन की तारीख से लागू हुए; दूसरा समूह एक वर्ष बाद और मुख्य समूह अठारह महीने बाद निर्धारित है (Gazette की तारीख से गणना करने पर 13 मई 2027)। किन धाराओं की कौन-सी तारीख है, यह अधिसूचना में देखें। यह न मानें कि सभी मुख्य दायित्व आज ही लागू हैं。",
      "refs": ["commencement", "act"]
    },
    {
      "id": "rules", "keys": ["dpdp rules", "rules 2025", "rules", "नियम", "rules kya"],
      "en": "The Digital Personal Data Protection Rules, 2025 were notified by MeitY as G.S.R. 846(E) on 13 November 2025. They set out operational details under the Act. Rule 1(2) provides for phased commencement of specified rules, so check the Gazette text and any corrigendum rather than assuming every rule began on the same date.",
      "hi": "Digital Personal Data Protection Rules, 2025 को MeitY ने 13 नवंबर 2025 को G.S.R. 846(E) के रूप में notify किया। ये Act के implementation की विस्तृत प्रक्रिया बताते हैं। Rule 1(2) कुछ नियमों के phased commencement का प्रावधान करता है, इसलिए सभी नियम एक ही दिन से लागू मानने के बजाय Gazette और corrigendum देखें。",
      "refs": ["rules", "commencement"]
    },
    {
      "id": "security", "keys": ["security safeguard", "reasonable security", "protect data", "सुरक्षा", "सिक्योरिटी"],
      "en": "The Act requires Data Fiduciaries to implement reasonable security safeguards to protect personal data in their possession or under their control, including measures to prevent personal data breaches. The Rules describe further safeguards and related requirements. See section 8 and the relevant Rules.",
      "hi": "Act के अनुसार Data Fiduciary को अपने कब्जे या नियंत्रण में मौजूद personal data की सुरक्षा के लिए उचित safeguards लागू करने होते हैं, जिनमें data breach रोकने के उपाय शामिल हैं। Rules में अतिरिक्त सुरक्षा आवश्यकताएँ दी गई हैं। धारा 8 और संबंधित Rules देखें。",
      "refs": ["act", "rules"]
    },
]

ALIASES = {
    "act": SOURCES[0], "rules": SOURCES[1], "commencement": SOURCES[2]
}

def answer_dpdp(question: str, language: str) -> dict:
    q = re.sub(r"\s+", " ", question.casefold()).strip()
    if len(q) < 3:
        raise HTTPException(status_code=422, detail="Please enter a DPDP-related question.")
    if len(q) > 700:
        raise HTTPException(status_code=422, detail="Question is too long (maximum 700 characters).")
    matches = []
    for item in FAQ:
        if any(key.casefold() in q for key in item["keys"]):
            matches.append(item)
    if not matches:
        return {
            "supported": False,
            "answer": ("I can answer only questions about India's Digital Personal Data Protection Act, 2023, its 2025 Rules and official commencement notifications. Try asking about consent, erasure, rights, children, data breaches or commencement."
                       if language == "en" else
                       "मैं केवल भारत के Digital Personal Data Protection Act, 2023, उसके 2025 Rules और आधिकारिक commencement notifications से जुड़े प्रश्नों का उत्तर दे सकता हूँ। Consent, erasure, rights, बच्चों के data, data breach या लागू होने की तारीख के बारे में पूछें।"),
            "sources": SOURCES,
            "note": "Curated offline knowledge base; not legal advice."
        }
    item = matches[0]
    return {
        "supported": True,
        "topic": item["id"],
        "answer": item["en"] if language == "en" else item["hi"],
        "sources": [ALIASES[x] for x in item["refs"]],
        "note": "Curated offline knowledge base; not legal advice."
    }
